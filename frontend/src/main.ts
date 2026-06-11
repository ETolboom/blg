import { createApp } from 'vue'
import router from './router'
import ToastService from 'primevue/toastservice';
import ConfirmationService from 'primevue/confirmationservice';
import PrimeVue from 'primevue/config';
import Aura from '@primeuix/themes/aura';
import Toast from 'primevue/toast';
import Tooltip from 'primevue/tooltip';
import App from './App.vue'

import 'bpmn-js/dist/assets/diagram-js.css';
import 'bpmn-js/dist/assets/bpmn-js.css';
import 'bpmn-js/dist/assets/bpmn-font/css/bpmn.css';
import 'primeicons/primeicons.css'

const app = createApp(App);

app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: "light"
        }
    },
});

app.component('Toast', Toast);
app.directive('tooltip', Tooltip);
app.use(ToastService);
app.use(ConfirmationService);
app.use(router);
app.mount('#app');

