<template>
  <div class="container">
    <div class="row">
      <div class="col">
        <div id="player"></div>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <h1>
          {{ title }}
          <span class="fs-3" v-if="! single">{{ num }}</span>
        </h1>
        <p>
          标签：
          <span v-for="label in labels">
            <span v-if="label==='H264'" class="badge text-bg-success">
              {{ label }}
            </span>
            <span v-else-if="label==='H265'" class="badge text-bg-danger">
              {{ label }}
            </span>
            <span v-else-if="label==='aac'" class="badge text-bg-success">
              {{ label }}
            </span>
            <span v-else class="badge text-bg-info">
              {{ label }}
            </span>
        </span>
        </p>
      </div>
    </div>
    <div class="row">
      <div :class="single?'col-12':'col-8'">
        <p>{{ description }}</p>
      </div>
      <div class="col-4" v-if="! single">
        <button type="button" class="btn btn-outline-light multiple" v-for="(item,index) in filelist"
                data-bs-toggle="tooltip" :data-bs-title="item.title" @click="play(index)">
          {{ padding(index + 1, Math.log(filelist.length) / Math.log(10)) }}
        </button>
      </div>
    </div>
  </div>
  <div class="btn-group mirror" role="group">
    <div class="btn-group" role="group">
      <button type="button" class="btn btn-warning dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
        Mirrors
      </button>
      <ul class="dropdown-menu">
        <li><a class="dropdown-item" target="_blank" :href="mirror+url" v-for="mirror in mirrors">{{ mirror }}</a></li>
      </ul>
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
const num = ref("")
const description = ref("")
const filelist = ref([])
const single = ref(true)
const labels = ref([])
const mirrors = ref([])
const url = ref("")
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
  await Axios.get("https://raw.githubusercontent.com/ipfs/public-gateway-checker/main/gateways.json").then((res) => {
    url.value = window.location.href.replace(/http[s]?:\/\/[^/]+/,"")
    mirrors.value = res.data
  })
  await Axios.get(files_json).then((res) => {
    cover = res.data["cover"]
    title.value = res.data.title
    description.value = res.data.description
    filelist.value = res.data.files
    if (filelist.value.length > 1) {
      single.value = false
      num.value = padding(1, Math.log(filelist.value.length) / Math.log(10))
    }
    play_video(res.data.files[0])
    label_check()
    if (res.data.labels !== undefined) {
      labels.value = labels.value.concat(res.data.labels)
    }
  });
}

function play_video(video_file) {
  if (single.value) {
    document.title = title.value + " IPFS Player"
  } else {
    document.title = title.value + " " + num.value + " IPFS Player"
  }
  const player = new xgplayer({
    id: 'player',
    url: video_file.url,
    plugins: video_file.type === "m3u8" ? [HlsJsPlugin] : [],
    height: "729",
    width: "1296",
    autoplay: true,
    poster: cover,
  });
  player.on(xgplayer.Events.CSS_FULLSCREEN_CHANGE, (isFullscreen) => {
    const playbox = document.getElementById("player")
    if (isFullscreen) {
      playbox.style.width = '100%'
      playbox.style.height = '100%'
    } else {
      playbox.style.width = "1296px"
      playbox.style.height = "729px"
    }
  })
}

function play(item) {
  num.value = padding(item + 1, Math.log(filelist.value.length) / Math.log(10))
  play_video(filelist.value[item])
}

function padding(num, length) {
  for (let len = (num + "").length; len < length; len = num.length) {
    num = "0" + num;
  }
  return num;
}

function label_check() {
  function label_add(label) {
    if (labels.value.indexOf(label) < 0) {
      labels.value.push(label)
    }
  }

  for (let i = 0; i < filelist.value.length; i++) {
    let mediainfo = filelist.value[i]["mediainfo"]
    for (let j = 0; j < mediainfo["streams"].length; j++) {
      let stream = mediainfo["streams"][j]
      if (stream["codec_type"] === "audio" || stream["codec_type"] === "video") {
        switch (stream["codec_name"]) {
          case  "h264":
            label_add("H264")
            break;
          case  "hevc":
            label_add("H265")
            break;
          case "aac":
            label_add("aac")
            break;
          default:
        }
      }
    }
  }
}
</script>
<style scoped>
#player {
  width: 1296px;
  height: 729px;
}

.multiple {
  margin: 0.2em;
}
.mirror {
  position: absolute;
  top: 2em;
  right: 2em;
}
</style>
