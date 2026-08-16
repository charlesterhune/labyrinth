<template>
    <div
        class="score-row"
        :class="[
            pieceIndexClass,
            { 'score-row--is-turn': isTurn }
        ]"
    >
        <v-player-piece
            :maxSize="25"
            :player="player"
            :svgSize="30"
            class="score-row__piece-symbol"
        />

        <div class="score-row__player-name">
            <player-name-panel :player="player" />
        </div>

        <p class="score-row__score-data">
            {{ player.score }}
        </p>
    </div>
</template>

<script>
import VPlayerPiece from "@/components/VPlayerPiece.vue";
import PlayerNamePanel from "@/components/PlayerNamePanel.vue";
import { NO_ACTION } from "@/model/player.js";

export default {
    name: "v-score-board-row",

    components: {
        VPlayerPiece,
        PlayerNamePanel,
    },

    props: {
        player: {
            required: true,
        },
    },

    computed: {
        pieceIndexClass() {
            return "score-row--player-" + this.player.pieceIndex;
        },

        isTurn() {
            return this.player.nextAction !== NO_ACTION;
        },
    },
};
</script>

<style lang="scss">
.score-row {
    height: var(--score-row-height);
    width: $game-widget-width;

    display: flex;
    flex-flow: row nowrap;
    align-items: center;

    border: 2px solid transparent;

    &--is-turn {
        border: 2px solid $interaction-color;
        @include drop-shadow;

        transform: scale(1.05);
        z-index: 10;
    }

    &--player-0 {
        background: $color-player-0-secondary;
    }

    &--player-1 {
        background: $color-player-1-secondary;
    }

    &--player-2 {
        background: $color-player-2-secondary;
    }

    &--player-3 {
        background: $color-player-3-secondary;
    }

    &__piece-symbol {
        width: 3rem;
        height: 2rem;
        flex: 0 0 3rem;
    }

    &__player-name {
    --text-height: calc(var(--score-row-height) - 0.2rem);
    flex: 1;
    width: auto;
    min-width: 0;
        height: var(--text-height);

        flex: 0 0 8rem;

        overflow: hidden;

        border-right: 1px solid $color-ui-border;

        box-sizing: border-box;
    }

    &__score-data {
        width: 2rem;
        flex: 0 0 2rem;

        margin: 0;
        padding-right: 0.5rem;

        text-align: right;
    }
}
</style>