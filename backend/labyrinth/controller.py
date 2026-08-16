""" Controller

handles database access, calls functions on entities or use cases, performs exception mapping
Should not contain business logic
"""
from datetime import timedelta

from flask import url_for, current_app

import labyrinth.model.factories as factory
import labyrinth.mapper.api as mapper
from labyrinth import exceptions
from labyrinth.database import DatabaseGateway
from labyrinth.model.exceptions import LabyrinthDomainException
from labyrinth.model import interactors
from labyrinth.model.game import Player
from labyrinth.model import bots

import labyrinth.event_logging as logging


# Treasure Kracken Level 7 board size
TREASURE_KRACKEN_MAZE_SIZE = 13


def add_player(game_id, player_request_dto):
    """Adds a player to a game.
    Creates the game if it does not exist.
    After adding the player, the game is started.
    """
    _ = interactors.OverduePlayerInteractor(
        game_repository(),
        logging.get_logger()
    )
    _ = interactors.UpdateOnTurnChangeInteractor(game_repository())

    game = _get_or_create_game(game_id)

    is_bot, computation_method = mapper.dto_to_type(player_request_dto)
    player_name = mapper.dto_to_player_name(player_request_dto)
    player_id = _try(game.unused_player_id)

    player = None

    if not is_bot:
        player = Player(
            player_id,
            player_name=player_name
        )
    else:
        player = _try(
            lambda: bots.create_bot(
                compute_method=computation_method,
                url_supplier=URLSupplier(),
                player_id=player_id,
                player_name=player_name
            )
        )

    _try(lambda: game.add_player(player))

    DatabaseGateway.get_instance().update_game(game_id, game)
    DatabaseGateway.get_instance().commit()

    logging.get_logger().add_player(
        player_id,
        game_id=game_id,
        is_bot=is_bot,
        num_players=len(game.players)
    )

    return mapper.player_to_dto(player)


def delete_player(game_id, player_id):
    """Removes a player from a game."""
    _ = interactors.OverduePlayerInteractor(
        game_repository(),
        logging.get_logger()
    )
    _ = interactors.UpdateOnTurnChangeInteractor(game_repository())

    game = _load_game_or_throw(game_id, for_update=True)

    _try(lambda: game.remove_player(player_id))

    DatabaseGateway.get_instance().update_game(game_id, game)
    DatabaseGateway.get_instance().commit()

    logging.get_logger().remove_player(
        player_id,
        game_id=game_id,
        num_players=len(game.players)
    )

    return ""


def change_player_name(game_id, player_id, player_name_dto):
    """Renames a player."""
    new_name = mapper.dto_to_player_name(player_name_dto)

    interactors.PlayerInteractor(
        game_repository()
    ).change_name(
        game_id,
        player_id,
        new_name
    )

    DatabaseGateway.get_instance().commit()


def change_game(game_id, game_request_dto):
    """
    Restart the game.

    Treasure Kracken Level 7 ALWAYS uses the huge 13x13 board,
    regardless of what size the client requests.
    """

    _ = interactors.OverduePlayerInteractor(
        game_repository(),
        logging.get_logger()
    )

    _ = interactors.UpdateOnTurnChangeInteractor(
        game_repository()
    )

    game = _load_game_or_throw(game_id)

    new_board = _try(
        lambda: factory.create_board(
            maze_size=TREASURE_KRACKEN_MAZE_SIZE
        )
    )

    _try(
        lambda: game.restart(new_board)
    )

    DatabaseGateway.get_instance().update_game(
        game_id,
        game
    )

    DatabaseGateway.get_instance().commit()


def get_game_state(game_id):
    """Returns the game state."""

    _ = interactors.OverduePlayerInteractor(
        game_repository(),
        logging.get_logger()
    )

    _ = interactors.UpdateOnTurnChangeInteractor(
        game_repository()
    )

    # IMPORTANT:
    # Force any previously saved 7x7/9x9 game to 13x13
    # before returning state to the browser.
    _force_huge_game(game_id)

    action_timeout = timedelta(
        seconds=int(
            current_app.config[
                "OVERDUE_PLAYER_TIMEDELTA_S"
            ]
        )
    )

    interactor = interactors.ObserveGameInteractor(
        game_repository(),
        action_timeout=action_timeout
    )

    game, remaining_timedelta = _try(
        lambda: interactor.retrieve_game(game_id)
    )

    game_state = mapper.game_state_to_dto(
        game,
        remaining_timedelta
    )

    DatabaseGateway.get_instance().commit()

    return game_state


def perform_shift(game_id, player_id, shift_dto):
    """Performs a shift operation on the game."""

    location, rotation = mapper.dto_to_shift_action(
        shift_dto
    )

    _ = interactors.OverduePlayerInteractor(
        game_repository(),
        logging.get_logger()
    )

    _ = interactors.UpdateOnTurnChangeInteractor(
        game_repository()
    )

    interactor = interactors.PlayerActionInteractor(
        game_repository()
    )

    _try(
        lambda: interactor.perform_shift(
            game_id,
            player_id,
            location,
            rotation
        )
    )

    DatabaseGateway.get_instance().commit()


def perform_move(game_id, player_id, move_dto):
    """Performs a move operation on the game."""

    location = mapper.dto_to_move_action(
        move_dto
    )

    _ = interactors.OverduePlayerInteractor(
        game_repository(),
        logging.get_logger()
    )

    _ = interactors.UpdateOnTurnChangeInteractor(
        game_repository()
    )

    interactor = interactors.PlayerActionInteractor(
        game_repository()
    )

    _try(
        lambda: interactor.perform_move(
            game_id,
            player_id,
            location
        )
    )

    DatabaseGateway.get_instance().commit()


def get_computation_methods():
    """Retrieves available bot computation methods."""

    return bots.get_available_computation_methods()


def remove_overdue_players(overdue_timedelta):
    """Removes players which block the game."""

    interactor = interactors.OverduePlayerInteractor(
        game_repository(),
        logging.get_logger()
    )

    _try(
        lambda: interactor.remove_overdue_players(
            overdue_timedelta
        )
    )

    DatabaseGateway.get_instance().commit()


def remove_unobserved_games(unobserved_period):
    """Removes games that have not been observed."""

    interactor = interactors.UnobservedGamesInteractor(
        game_repository(),
        logging.get_logger()
    )

    removed_ids = _try(
        lambda: interactor.remove_unobserved_games(
            unobserved_period
        )
    )

    for game_id in removed_ids:
        logging.get_logger().remove_game(game_id)

    DatabaseGateway.get_instance().commit()


def game_repository():
    return interactors.GameRepository(
        DatabaseGateway.get_instance()
    )


def _get_or_create_game(game_id):
    """
    Get the requested game.

    If it does not exist, create it as 13x13.

    If it already exists as 7x7 or 9x9,
    immediately rebuild it as 13x13.
    """

    game = DatabaseGateway.get_instance().load_game(
        game_id
    )

    if game is None:
        game = _create_game(game_id)

    else:
        game = _ensure_huge_board(
            game_id,
            game
        )

    return game


def _create_game(game_id):
    """
    Create every new Treasure Kracken game as 13x13.
    """

    game = factory.create_game(
        maze_size=TREASURE_KRACKEN_MAZE_SIZE,
        game_id=game_id
    )

    DatabaseGateway.get_instance().create_game(
        game,
        game_id
    )

    DatabaseGateway.get_instance().commit()

    logging.get_logger().add_game(
        game_id
    )

    return game


def _load_game_or_throw(game_id, for_update=False):
    """
    Load a game and ensure it is using the huge board.
    """

    game = DatabaseGateway.get_instance().load_game(
        game_id,
        for_update=for_update
    )

    if game is None:
        raise exceptions.GAME_NOT_FOUND_API_EXCEPTION

    return _ensure_huge_board(
        game_id,
        game
    )


def _force_huge_game(game_id):
    """
    Used by get_game_state so even old stored games
    are automatically converted to 13x13.
    """

    game = DatabaseGateway.get_instance().load_game(
        game_id
    )

    if game is None:
        return

    _ensure_huge_board(
        game_id,
        game
    )


def _ensure_huge_board(game_id, game):
    """
    If this saved game is not 13x13, rebuild it.

    Existing players stay attached to the game object.
    """

    try:
        current_size = game.board.maze.size
    except AttributeError:
        current_size = None

    if current_size == TREASURE_KRACKEN_MAZE_SIZE:
        return game

    new_board = factory.create_board(
        maze_size=TREASURE_KRACKEN_MAZE_SIZE
    )

    game.restart(
        new_board
    )

    DatabaseGateway.get_instance().update_game(
        game_id,
        game
    )

    DatabaseGateway.get_instance().commit()

    return game


def _try(model_operation):
    """Performs the given model operation."""

    try:
        return model_operation()

    except LabyrinthDomainException as domain_exception:
        raise exceptions.domain_to_api_exception(
            domain_exception
        )


class URLSupplier:
    """Supplies request URLs for the API."""

    def get_shift_url(
        self,
        game_id,
        player_id
    ):
        return self._get_url(
            game_id,
            player_id,
            "api.post_shift"
        )

    def get_move_url(
        self,
        game_id,
        player_id
    ):
        return self._get_url(
            game_id,
            player_id,
            "api.post_move"
        )

    def _get_url(
        self,
        game_id,
        player_id,
        api_method
    ):

        internal_url = (
            current_app.config["INTERNAL_URL"]
            if "INTERNAL_URL" in current_app.config
            else None
        )

        if internal_url:

            return internal_url + url_for(
                api_method,
                game_id=game_id,
                p_id=player_id,
                _external=False
            )

        return url_for(
            api_method,
            game_id=game_id,
            p_id=player_id,
            _external=True
        )