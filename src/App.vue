<template>
  <div>
    <div id="player"></div>
  </div>
</template>

<script setup>
import {onMounted} from 'vue'
import Axios from 'axios'
import xgplayer from 'xgplayer';
import HlsJsPlugin from 'xgplayer-hls.js';
import 'xgplayer/dist/index.min.css';

onMounted(() => {
  init()
})
let cover = ""
async function init(){
  let hash = window.location.hash;
  let files_json_file = "./files.json"
  if (hash !== "") {
    let files_json = hash.match("files.json=(.*)")
    if (files_json !== null) {
      files_json_file = files_json[1]
      if (files_json_file.substr(0, 6) !== "/ipfs/") {
        files_json_file = "/ipfs/" + files_json_file
      }
    }
  }
  await Axios.get(files_json_file).then((res) => {
    cover = res.data.cover
    play_video(res.data.files[0])
  });
}
function play_video(video_file) {
  new xgplayer({
    id: 'player',
    url: video_file.url,
    plugins: video_file.type === "m3u8" ? [HlsJsPlugin] : [],
    height: "720",
    width: "1280",
    autoplay: true,
    poster: cover,
  });
}

</script>


<style scoped>
#player {
  width: 1280px;
  height: 720px;
}

</style>
