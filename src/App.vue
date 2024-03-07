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
