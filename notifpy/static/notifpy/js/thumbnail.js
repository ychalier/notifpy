let images = document.querySelectorAll("img.video__thumbnail");
for (let i = 0; i < images.length; i++) {
    images[i].onload = function() {
        if (images[i].naturalWidth == 120) {
            images[i].src = images[i].src.replace("maxresdefault", "mqdefault");
        } else if (images[i].naturalWidth == 320) {
            let target = images[i];
            let maxres = target.src.replace("mqdefault", "maxresdefault");
            let dummy = new Image;
            dummy.onload = function() {
                if (dummy.width != 120) {
                    target.src = dummy.src;
                }
            }
            dummy.src = maxres;
        }
    }
}
