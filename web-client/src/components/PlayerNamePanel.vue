<template>
    <v-editable-field
        v-if="isEditable"
        v-model="playerName"
        :placeholder="editablePlaceholder"
    />
    <p v-else>{{ playerLabel }}</p>
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
        ...mapActions(usePlayersStore, ["changeUserPlayerName"]),

        receiveWixPlayerName(event) {
            const data = event.data;

            if (!data || data.type !== "SET_PLAYER_NAME") {
                return;
            }

            if (!this.player.isUser) {
                return;
            }

            if (!data.playerName) {
                return;
            }

            const cleanName = String(data.playerName).trim();

            if (!cleanName) {
                return;
            }

            console.log("Wix player name received:", cleanName);

            this.changeUserPlayerName(cleanName);
        },
    },

    mounted() {
        window.addEventListener("message", this.receiveWixPlayerName);
    },

    beforeUnmount() {
        window.removeEventListener("message", this.receiveWixPlayerName);
    },
};
</script>

<style></style>