<template>
  <div class="container">
    <div class="row">
      <div class="col">
        <div id="player"></div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <h1>{{ title }}</h1>
      </div>
    </div>
    <div class="row">
      <div class="col-8">
        <p>{{ description }}</p>
      </div>
      <div class="col-4">
        <button type="button" class="btn btn-outline-light multiple" v-for="(item,index) in filelist" data-bs-toggle="tooltip" :data-bs-title="item.title" @click="play(index)">
          {{ padding(index + 1, Math.log(filelist.length) / Math.log(10))}}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted} from 'vue'
import Axios from 'axios'
import xgplayer from 'xgplayer';
import HlsJsPlugin from 'xgplayer-hls.js';
import 'xgplayer/dist/index.min.css';

onMounted(() => {
  init()
})
let cover = ""
const title = ref("")
const description = ref("")
const filelist = ref([])
async function init() {
  let hash = window.location.hash;
  let files_json = "./files.json"

  if (hash !== "") {
    let files_json_hash = hash.match("files.json=(.*)")
    if (files_json_hash !== null) {
      files_json = files_json_hash[1]
      if (files_json.slice(0, 6) !== "/ipfs/") {
        files_json = "/ipfs/" + files_json
      }
    }
  }
  await Axios.get(files_json).then((res) => {
    cover = res.data.cover
    title.value = res.data.title
    description.value = res.data.description
    play_video(res.data.files[0])
    filelist.value = res.data.files
  });
}

function play_video(video_file) {
  new xgplayer({
    id: 'player',
    url: video_file.url,
    plugins: video_file.type === "m3u8" ? [HlsJsPlugin] : [],
    height: "729",
    width: "1296",
    autoplay: true,
    poster: cover,
  });
}
function play(item) {
  play_video(filelist.value[item])
}
function padding(num, length) {
  for(let len = (num + "").length; len < length; len = num.length) {
   num = "0" + num;
  }
  return num;
 }
</script>
<style scoped>
#player {
  width: 1296px;
  height: 729px;
}
.multiple{
  margin: 0.2em;
}
</style>
