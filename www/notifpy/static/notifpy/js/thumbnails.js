let imgs = document.querySelectorAll(".video__thumbnail");
for (let i = 0; i < imgs.length; i++) {
    maxres = imgs[i].src.replace("mqdefault", "maxresdefault");
    let img = new Image;
    let target = imgs[i];
    img.onload = function() {
        if (img.width != 120) {
            target.src = img.src;
        }
    };
    img.src = maxres;
}
