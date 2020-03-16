console.log("Echo from thumbnail.js");

let images = document.querySelectorAll("img.video__thumbnail__background");

function set_thumbnail_source(target) {
    let dummy = new Image;
    dummy.onload = function() {
        if (dummy.width != 120) {
            let parent = target.parentNode;
            // console.log(parent);
            let newNode = document.createElement("img");
            newNode.src = dummy.src;
            newNode.className = "video__thumbnail__foreground";
            parent.appendChild(newNode);
            setTimeout(() => {
                newNode.classList.add("video__thumbnail__foreground--shown");
            }, 100);
        } else {
            let alt_dummy = new Image;
            alt_dummy.onload = function() {
                if (alt_dummy.width != 120) {
                    target.src = alt_dummy.src;
                }
            }
            alt_dummy.src = target.getAttribute("true_src").replace("maxresdefault", "mqdefault");
        }
    }
    dummy.src = target.getAttribute("true_src").replace("mqdefault", "maxresdefault");
}
for (let i = 0; i < images.length; i++) {
    set_thumbnail_source(images[i]);
}
