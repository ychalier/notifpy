function send_request(method, url, body, callback) {
    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            callback(xhttp.responseText);
        }
    }
    xhttp.open(method, url);
    xhttp.setRequestHeader("X-CSRFToken", token);
    xhttp.send(body);
}
