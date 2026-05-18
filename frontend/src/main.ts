import { createApp } from "vue";
import { createPinia } from "pinia";
import Buefy from "buefy";

import "bulma/css/bulma.min.css";
import "buefy/dist/css/buefy.min.css";
import "@mdi/font/css/materialdesignicons.min.css";
import "@fortawesome/fontawesome-free/css/all.min.css";
import "./styles/dark.css";

import App from "./App.vue";

const app = createApp(App);
app.use(createPinia());
app.use(Buefy);
app.mount("#app");
