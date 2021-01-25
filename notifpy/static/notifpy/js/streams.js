console.log("Echo from stream.js");
console.log("Stream route: " + STREAMS_ROUTE);

let request = new XMLHttpRequest();
request.open("GET", STREAMS_ROUTE, true);

var template = document.querySelector("#template--stream");
var streamList = document.querySelector("#stream_list");
var loaded = 0;

function appendStream(data, i) {
    let clone = document.importNode(template.content, true);
    let icon = clone.querySelector("figure.avatar img");
    icon.alt = data[i].name;
    icon.src = data[i].thumb;
    clone.querySelector("figure a").href = data[i].lnk;
    clone.querySelector(".card-image img").src = data[i].screen;
    clone.querySelector(".card-title").textContent = data[i].name;
    clone.querySelector(".card-subtitle").textContent = data[i].game;
    clone.querySelector(".card-body").textContent = data[i].title;
    clone.querySelector(".viewer-count").textContent = data[i].viewer_count;
    let elapsed = Math.round((Date.now() - Date.parse(data[i].started_at)) / 1000); // stream elapsed time in seconds
    let elapsedHours = Math.floor(elapsed / 3600);
    let elapsedMinutes = Math.round((elapsed - elapsedHours * 3600) / 60);
    let elapsedMinutesPadded = elapsedMinutes < 10 ? "0" + elapsedMinutes.toString() : elapsedMinutes.toString();
    clone.querySelector(".started-at").textContent = elapsedHours + "h" + elapsedMinutesPadded;
    streamList.appendChild(clone);
}

request.onload = function() {
    if (request.readyState === 4 && request.status == 200) {
        let data = JSON.parse(request.response);
        console.log("Found " + data.length + " stream(s)");
        streamList.innerHTML = "";
        if (data.length > 0) {
            for (let i = 0; i < data.length; i++) {
                appendStream(data, i);
            }
        } else {
            streamList.innerHTML = "<span class='message'>No active stream.</span>";
        }
    }
}

request.send(null);