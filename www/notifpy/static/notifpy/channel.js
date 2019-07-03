
var token = document.querySelector("input[name='csrfmiddlewaretoken']").value;
document.querySelector("#submit").addEventListener("click", (event) => {
    event.preventDefault();
    let input = document.querySelector("#input");
    let query = input.value;
    if (query != "") {
        console.log(query);
        input.value = "";
        let xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                let data = JSON.parse(xhttp.responseText);
                let div = document.querySelector("#results");
                let h2 = document.createElement("h2");
                h2.innerHTML = "Results";
                div.appendChild(h2);
                for (let i = 0; i < data.length; i++) {
                    let template = document.importNode(document.querySelector("#template").content, true);
                    template.querySelector("img").setAttribute("src", data[i].thumbnail);
                    template.querySelector("span").innerHTML = data[i].title;
                    template.querySelector("input[name='title']").setAttribute("value", data[i].title);
                    template.querySelector("input[name='thumbnail']").setAttribute("value", data[i].thumbnail);
                    template.querySelector("input[name='id']").setAttribute("value", data[i].id);
                    div.appendChild(template);
                }
            }
        }
        xhttp.open("POST", "/notifpy/api/find-channel");
        xhttp.setRequestHeader("X-CSRFToken", token);
        xhttp.send(query);
    }
})
