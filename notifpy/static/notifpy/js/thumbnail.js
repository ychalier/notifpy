// console.log("Echo from thumbnail.js");

document.querySelectorAll("img.youtube_thumbnail_fg").forEach((target) => {
    let dummy = new Image;
    dummy.onload = function() {
        if (dummy.width != 120) {
            target.src = dummy.src;
            setTimeout(() => {
                target.classList.add("show");
            }, 100);
        } else {
            let alt_dummy = new Image;
            alt_dummy.onload = function() {
                if (alt_dummy.width != 120) {
                    target.src = alt_dummy.src;
                    setTimeout(() => {
                        target.classList.add("show");
                    }, 100);
                }
            }
            alt_dummy.src = target.getAttribute("lazysrc").replace("maxresdefault", "mqdefault");
        }

    }
    dummy.src = target.getAttribute("lazysrc").replace("mqdefault", "maxresdefault");
});