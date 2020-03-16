console.log("Echo from stream.js");
console.log("Stream route: " + STREAMS_ROUTE);

let request = new XMLHttpRequest();
request.open("GET", STREAMS_ROUTE, true);

var template = document.querySelector("#template--stream");
var streamList = document.querySelector("#stream_list");
streamList.innerHTML = "";
var loaded = 0;

function appendStream(data, i) {
    let clone = document.importNode(template.content, true);
    let icon = clone.querySelector(".channel__thumbnail");
    icon.alt = data[i].name;
    icon.onload = function () {
        loaded++;
        if (loaded === data.length) {
            streamList.classList.add("stream_banner--expanded");
        }
    }
    clone.querySelector(".image-link").href = data[i].lnk;
    clone.querySelector(".tooltip__user").textContent = data[i].name;
    clone.querySelector(".tooltip__game").textContent = data[i].game;
    clone.querySelector(".tooltip__title").textContent = data[i].title;
    clone.querySelector(".tooltip__screen").src = data[i].screen;
    icon.src = data[i].thumb;
    streamList.appendChild(clone);
}

request.onload = function() {
    if (request.readyState === 4 && request.status == 200) {
        let data = JSON.parse(request.response);
        console.log("Found " + data.length + " stream(s)");
        for (let i = 0; i < data.length; i++) {
            appendStream(data, i);
        }
        setTimeout(() => {
            streamList.classList.add("stream_banner--expanded");
        }, 1000);
    }
}

request.send(null);
