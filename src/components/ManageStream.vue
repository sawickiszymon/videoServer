<template>
  <div class="mt-3">
    <div class="text-center mt-4"> Current media: {{ streams.length }}
      <button v-on:click.prevent="Manage('Refresh')" type="button" class="btn btn-sm btn-outline-secondary ml-4">Refresh</button>
      <button v-if="!isPaused" v-on:click.prevent="Manage('Pause')" type="button" class="btn btn-sm btn-outline-secondary ml-4">Pause</button>
      <button v-if="isPaused" v-on:click="Manage('Resume')" type="button" class="btn btn-sm btn-outline-secondary ml-4">Resume</button>
    </div>

    <div v-for="stream in streams" class="media-body p-3 lh-125 border-bottom border-gray" style="width: 100%; height: 100%" v-bind:key="stream">
      <div class="justify-content-between align-items-center">
        <a v-on:click.prevent="SelectStreamTo('Start', stream)"  href="#">{{ stream.key }}</a>
        <button v-on:click="SelectStreamTo('Delete', stream)" type="button" class="btn btn-sm btn-outline-secondary ml-4">Delete</button>
      </div>
      <span class="d-block">{{ stream.uri }}</span>
    </div>
  </div>
</template>

<script>
export default {
name: "ManageStream",
  props: ['form', 'streams', 'isPaused', 'stream', 'wsavc', 'playing'],
  method: {type: Function},
  methods: {
    SelectStreamTo: async function(activity, stream){
      this.stream = stream
      switch(activity) {
        case "Start":
          await this.$emit('show-stream', this.stream)
          break;
        case "Delete":
          await this.deleteStream(stream)
          break;
      }
    },
    Manage: async function(activity){
      switch(activity) {
        case "Refresh":
          await this.$emit('refresh-stream')
          break;
        case "Pause":
          await this.pauseStream()
          break;
        case "Resume":
          await this.resumeStream()
          break;
      }
    },
    resumeStream: async function() {
      try {
        const unPause = 0x100
        this.wsavc.send(unPause)
        let isPaused = false
        await this.$emit('get-paused', isPaused)
      } catch (err) {
        this.form.error = err
      }
    },

    pauseStream: async function() {
      try {
        const closeWs = 0x101
        this.wsavc.send(closeWs)
        let isPaused = true
        await this.$emit('get-paused', isPaused)
        await this.$emit('remove-canvas', false)
      } catch (err) {
        this.form.error = err
      }
    },
    deleteStream: async function (stream) {
      console.log(stream.uri)
      this.form.options.should_end = true
      const data = {
        uri: stream.uri,
        options: {
          should_end: this.form.options.should_end,
        }
      };

      try {
        const BASE_URL = process.env.VUE_APP_BASEURL

        // eslint-disable-next-line no-unused-vars
        const response = await this.$http.post(BASE_URL + '/stream/manage', data);
        let playing = false
        console.log(this.streams)
        await this.$emit('remove-canvas', playing)
        await this.$emit('refresh-stream')
      } catch (err) {
        this.form.error = err
      }
    },

  }

}

</script>

<style scoped>

</style>