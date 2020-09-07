<template>
  <form v-on:submit.prevent="createStream" style="display:inline-block;width: 600px" >
    <div v-if="form.error" class="alert alert-danger" role="alert">{{ form.error }}</div>
    <div class="form-row" >
      <div class="form-group col">
        <div class="input-group">
          <input id="uri" v-model="form.uri" aria-describedby="uriHelp" class="form-control" placeholder="Enter uri"
                 required type="text">
          <span class="input-group-append">
              <button  v-on:submit.prevent="createStream" type="submit" class="btn btn-primary">Get stream</button>
            </span>
        </div>
        <small id="uriHelp" class="form-text text-muted">Add IP Camera, URL example: rtsp://user:password@ip:port/path</small>
      </div>
    </div>

    <a data-toggle="collapse" href="#details" role="button" aria-expanded="false" aria-controls="collapseExample" >
      Show more options
    </a>

    <div class="form-row collapse" id="details">
      <div class="form-group col">
        <label for="width">Width, px</label>
        <input v-model="form.options.width" name="width" class="form-control" id="width" type="number"/>
      </div>
      <div class="form-group col">
        <label for="height">Height, px</label>
        <input v-model="form.options.height" name="height" class="form-control" id="height" type="number"/>
      </div>
    </div>
  </form>
</template>

<script>
export default {
name: "StreamCreation",
  props: ['stream', 'form'],
  methods: {
    method: {type : Function },
    createStream: async function () {
      this.form.options.should_end = false
      const data = {
        uri: this.form.uri,
        options: {
          should_end: this.form.options.should_end,
          height: parseInt(this.form.options.height),
          width: parseInt(this.form.options.width),
        }
      };

      try {
        const BASE_URL = process.env.VUE_APP_BASEURL
        const response = await this.$http.post(BASE_URL + '/stream/manage', data);
        await this.$emit('refresh-stream')
        await this.$emit('show-stream', response.data)
      } catch (err) {
        this.error = err
      }
    },
  }
}
</script>

<style scoped>

</style>