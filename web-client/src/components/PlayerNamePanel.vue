<template>
    <div class="player-name-panel">

        <img
            v-if="isUserPlayer && profilePic"
            :src="profilePic"
            class="player-name-panel__avatar"
            alt=""
        />

        <v-editable-field
            v-if="isEditable"
            v-model="playerName"
            :placeholder="editablePlaceholder"
        />

        <p v-else>
            {{ playerLabel }}
        </p>

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
            profilePic: "",
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
            ["changeUserPlayerName"]
        ),

        receiveWixPlayerInfo(event) {
            const data = event.data;

            if (
                !data ||
                data.type !== "SET_PLAYER_INFO"
            ) {
                return;
            }

            if (!this.player.isUser) {
                return;
            }

            if (data.playerName) {
                const cleanName =
                    String(data.playerName).trim();

                if (cleanName) {
                    this.changeUserPlayerName(
                        cleanName
                    );
                }
            }

            if (data.profilePic) {
                this.profilePic =
                    String(data.profilePic);
            }

            console.log(
                "Wix player info received:",
                data.playerName,
                data.profilePic
            );
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
    display: flex;
    align-items: center;
    gap: 8px;
}

.player-name-panel__avatar {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    object-fit: cover;
    flex-shrink: 0;
    border: 2px solid #9149D6;
}
</style>