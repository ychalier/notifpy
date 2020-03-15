console.log("Echo from stream.js");
console.log("Stream route: " + STREAMS_ROUTE);

let request = new XMLHttpRequest();
request.open("GET", STREAMS_ROUTE, true);

request.onload = function() {
    if (request.readyState === 4 && request.status == 200) {
        let data = JSON.parse(request.response);
        console.log("Found " + data.length + " stream(s)");
        let template = document.querySelector("#template--stream");
        let streamList = document.querySelector("#stream_list");
        streamList.innerHTML = "";
        for (let i = 0; i < data.length; i++) {
            let clone = document.importNode(template.content, true);
            clone.querySelector(".image-link").href = data[i].link;
            clone.querySelector(".channel__thumbnail").src = data[i].thumb;
            clone.querySelector(".channel__thumbnail").alt = data[i].name;
            clone.querySelector(".tooltip__text").textContent = data[i].game + " • " + data[i].title;
            streamList.appendChild(clone);
        }
    }
}

request.send(null);
