import { defineStore } from "pinia";
import { useGameStore } from "@/stores/game.js";
import { usePlayersStore } from "@/stores/players.js";

import { NO_ACTION } from "@/model/player.js";

export const useCountdownStore = defineStore("countdown", {
    state: () => ({
        timer: 0,
        remainingSeconds: 0,

        // Remember which turn/action this timer belongs to.
        activePlayerId: null,
        activeAction: null,
    }),

    getters: {
        isRunning: (state) => state.timer !== 0,

        timerShouldRun: () => {
            const gameStore = useGameStore();
            const playersStore = usePlayersStore();
            const userPlayer = playersStore.userPlayer;

            if (!userPlayer) {
                return false;
            }

            return (
                userPlayer.nextAction !== NO_ACTION &&
                gameStore.isOnline
            );
        },
    },

    actions: {
        restartCountdown(newValue) {
            this.stopCountdown();

            this.resetRemainingSeconds(newValue);

            const timer = setInterval(() => {
                this.countDown();

                if (this.remainingSeconds <= 0) {
                    if (this.timerShouldRun) {
                        const playersStore =
                            usePlayersStore();

                        const gameStore =
                            useGameStore();

                        const currentPlayerId =
                            gameStore.nextAction?.playerId;

                        if (
                            currentPlayerId !== undefined &&
                            currentPlayerId !== null
                        ) {
                            playersStore.removeClientPlayer(
                                currentPlayerId
                            );
                        }
                    }

                    this.stopCountdown();
                    this.clearRemainingSeconds();
                    this.clearActiveAction();
                }
            }, 1000);

            this.saveTimer(timer);
        },

        stopCountdown() {
            if (this.timer !== 0) {
                clearInterval(this.timer);
                this.clearTimer();
            }
        },

        nextActionUpdated(nextAction) {
            if (!this.timerShouldRun || !nextAction) {
                this.stopCountdown();
                this.clearRemainingSeconds();
                this.clearActiveAction();
                return;
            }

            const playerId =
                nextAction.playerId;

            const action =
                nextAction.action;

            const remainingSecondsApi =
                nextAction.remainingSeconds ?? 0;

            const isNewTurn =
                this.activePlayerId !== playerId ||
                this.activeAction !== action;

            /*
             * Only START/RESTART when the actual turn changes.
             *
             * Do NOT restart every time the server polls.
             */
            if (isNewTurn) {
                this.activePlayerId =
                    playerId;

                this.activeAction =
                    action;

                this.restartCountdown(
                    remainingSecondsApi
                );

                return;
            }

            /*
             * Same turn:
             * only correct the local timer if it has drifted
             * significantly away from the server.
             *
             * A 1-second difference is normal because server
             * polling occurs every ~850ms.
             */
            const difference =
                Math.abs(
                    this.remainingSeconds -
                    remainingSecondsApi
                );

            if (difference > 2) {
                this.resetRemainingSeconds(
                    remainingSecondsApi
                );
            }
        },

        saveTimer(timer) {
            this.timer = timer;
        },

        clearTimer() {
            this.timer = 0;
        },

        resetRemainingSeconds(seconds) {
            this.remainingSeconds =
                Math.max(
                    0,
                    Number(seconds) || 0
                );
        },

        clearRemainingSeconds() {
            this.remainingSeconds = 0;
        },

        clearActiveAction() {
            this.activePlayerId = null;
            this.activeAction = null;
        },

        countDown() {
            if (this.remainingSeconds > 0) {
                this.remainingSeconds--;
            }
        },
    },
});