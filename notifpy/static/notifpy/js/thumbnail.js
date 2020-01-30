let images = document.querySelectorAll("img.video__thumbnail");

function set_thumbnail_source(target) {
    let dummy = new Image;
    dummy.onload = function() {
        if (dummy.width != 120) {
            target.src = dummy.src;
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
