<template>
    <div class="player-name-panel">
        <div class="player-name-panel__avatar-slot">
            <img
                v-if="isUserPlayer && profilePic"
                :src="profilePic"
                class="player-name-panel__avatar"
                alt=""
            />
        </div>

        <div class="player-name-panel__name">
            <v-editable-field
                v-if="isEditable"
                v-model="playerName"
                :placeholder="editablePlaceholder"
            />

            <p v-else>
                {{ playerLabel }}
            </p>
        </div>

        <div class="player-name-panel__spacer"></div>
    </div>
</template>

<script>
import VEditableField from "@/components/VEditableField.vue";
import { getLabel } from "@/model/player.js";

import { mapActions } from "pinia";
import { usePlayersStore } from "@/stores/players.js";

export default {
    name: "player-name-panel",

    components: {
        VEditableField,
    },

    data() {
        return {
            editablePlaceholder: "Player",
        };
    },

    props: {
        player: {
            required: true,
        },
    },

    computed: {
        isEditable() {
            return this.player.isUser;
        },

        isUserPlayer() {
            return this.player.isUser;
        },

        profilePic() {
            return this.player.profilePic || "";
        },

        playerLabel() {
            return getLabel(this.player);
        },

        playerName: {
            get() {
                return this.player.name;
            },

            set(value) {
                this.changeUserPlayerName(value);
            },
        },
    },

    methods: {
        ...mapActions(
            usePlayersStore,
            [
                "changeUserPlayerName",
                "setUserProfilePic",
            ]
        ),

        receiveWixPlayerInfo(event) {
            const data = event.data;

            if (
                !data ||
                data.type !== "SET_PLAYER_INFO"
            ) {
                return;
            }

            if (data.playerName) {
                const cleanName =
                    String(
                        data.playerName
                    ).trim();

                if (cleanName) {
                    this.changeUserPlayerName(
                        cleanName
                    );
                }
            }

            if (data.profilePic) {
                const cleanPic =
                    String(
                        data.profilePic
                    ).trim();

                if (cleanPic) {
                    this.setUserProfilePic(
                        cleanPic
                    );
                }
            }
        },
    },

    mounted() {
        window.addEventListener(
            "message",
            this.receiveWixPlayerInfo
        );
    },

    beforeUnmount() {
        window.removeEventListener(
            "message",
            this.receiveWixPlayerInfo
        );
    },
};
</script>

<style scoped>
.player-name-panel {
    width: 100%;
    height: 100%;

    display: grid;
    grid-template-columns:
        30px minmax(0, 1fr) 30px;

    align-items: center;

    box-sizing: border-box;
}

.player-name-panel__avatar-slot {
    width: 30px;

    display: flex;
    justify-content: center;
    align-items: center;
}

.player-name-panel__avatar {
    width: 28px;
    height: 28px;

    border-radius: 50%;
    object-fit: cover;

    border: 2px solid #9149D6;

    box-sizing: border-box;
}

.player-name-panel__name {
    min-width: 0;

    display: flex;
    justify-content: center;
    align-items: center;

    text-align: center;
    overflow: hidden;
}

.player-name-panel__name p {
    width: 100%;

    margin: 0;

    font-size: 12px;
    line-height: 1;

    text-align: center;

    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.player-name-panel__name > * {
    max-width: 100%;
}

.player-name-panel__spacer {
    width: 30px;
}
</style>