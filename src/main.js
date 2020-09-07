import Vue from 'vue'
import App from './App.vue'
// import 'bootstrap/dist/css/bootstrap.min.css';

import router from "@/router";
import VueResource from 'vue-resource';
import LoadScript from 'vue-plugin-load-script';
import visibility from 'vue-visibility-change';

// registry directive
Vue.use(visibility);
Vue.use(LoadScript);
Vue.config.productionTip = false
Vue.use(VueResource)

new Vue({
  router,
  render: h => h(App),
}).$mount('#app')
