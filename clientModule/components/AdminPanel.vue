<template>
  <div id="app" class="container" style="max-width: 1280px">
    <div class="text-center">
      <h2>Video surveillance system</h2>
    </div>

    <StreamCreation class="mt-4" v-bind:form="form" @refresh-stream="refreshStreams" @show-stream="showStream"/>

    <div class="d-flex justify-content-center" style="position: relative;">
      <div v-if="!playing" class="d-flex justify-content-center"
           style="width: 640px; height: 360px; background: black">
        <h2 class="align-self-center">No video</h2>
      </div>
      <div id="video-box"></div>
    </div>

    <ManageStream v-bind:streams="streams" v-bind:form="form" v-bind:wsavc="wsavc" v-bind:playing="playing" v-bind:isPaused="isPaused" v-bind:stream="stream"
                  @refresh-stream="refreshStreams" @show-stream="showStream" @get-paused="getIsPaused" @remove-canvas="removeCanvas"/>
  </div>
</template>

<script>
import ManageStream from "@/components/ManageStream";
import StreamCreation from "@/components/StreamCreation";
import WSAvcPlayer from 'ws-avc-player'

export default {
  name: "AdminPanel",
  components: {StreamCreation, ManageStream},
  data() {
    return {
      streams: [],
      form: {
        uri: null,
        options: {
          height: null,
          should_end: false,
          width: null,
        },
        error: null,
      },
      stream: null,
      wsavc: null,
      playing: false,
      isPaused: false,
    }
  },
  methods: {
    refreshStreams: async function() {
      const BASE_URL = process.env.VUE_APP_BASEURL
      const response = await this.$http.get(BASE_URL + '/stream');
      this.streams = response.data.streams;
    },
    getWSUrl: function(ws) {
      const BASE_URL = process.env.VUE_APP_BASEURL
      const ws_url = BASE_URL.replace(/(http)(s)?:\/\//, "ws$2://");
      return ws_url.replace(/\/$/,"") + '/' + ws.replace(/^\//,"");
    },

    showStream: async function(stream) {

      this.stream = stream
      this.playing = true
      this.isPaused = false

      const player_canvas = document.getElementById('video-box');
      if (this.wsavc) {
        await this.removeCanvas(this.playing)
      }

      this.wsavc = new WSAvcPlayer({userWorker:true})
      player_canvas.appendChild(this.wsavc.AvcPlayer.canvas)


      this.wsavc.connect(this.getWSUrl(this.stream.ws));
      },
    getIsPaused: async function(value){
      this.isPaused = value
    },
    removeCanvas: async function(value) {
      const e = document.getElementById('video-box')
      if (e.hasChildNodes()) {
        this.playing = value
        let child = e.lastElementChild
        e.removeChild(child)
      }
      this.wsavc.destroy
    },
  },

  created: async function() {
    await this.refreshStreams();
  }
};

</script>