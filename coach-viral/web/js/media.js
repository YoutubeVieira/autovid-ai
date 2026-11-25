/* Préparation des fichiers dans le navigateur : images extraites d'une vidéo, captures réduites.
   Rien n'est envoyé tant que l'utilisateur ne lance pas l'analyse. */
(function (g) {
  var MAX_SIDE = 768;

  function toJpeg(source, w, h) {
    var scale = Math.min(1, MAX_SIDE / Math.max(w, h));
    var c = document.createElement("canvas");
    c.width = Math.round(w * scale);
    c.height = Math.round(h * scale);
    c.getContext("2d").drawImage(source, 0, 0, c.width, c.height);
    return c.toDataURL("image/jpeg", 0.72);
  }

  function seek(video, t) {
    return new Promise(function (resolve, reject) {
      var done = function () { video.removeEventListener("seeked", done); resolve(); };
      video.addEventListener("seeked", done);
      video.addEventListener("error", function () { reject(new Error("Vidéo illisible dans ce navigateur.")); }, { once: true });
      video.currentTime = t;
    });
  }

  /* Renvoie { duree, images: [dataURL...] } : la première image au tout début (l'accroche), puis réparties. */
  async function framesFromVideo(file, count) {
    count = count || 6;
    var url = URL.createObjectURL(file);
    var video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    video.preload = "auto";
    video.src = url;
    try {
      await new Promise(function (resolve, reject) {
        video.onloadedmetadata = resolve;
        video.onerror = function () { reject(new Error("Format vidéo non pris en charge par ce navigateur.")); };
      });
      var d = isFinite(video.duration) ? video.duration : 0;
      var times = [Math.min(0.3, d / 10)];
      for (var i = 1; i < count; i++) times.push((d * i) / count);
      var images = [];
      for (var k = 0; k < times.length; k++) {
        await seek(video, times[k]);
        images.push(toJpeg(video, video.videoWidth, video.videoHeight));
      }
      return { duree: d, images: images };
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  async function shrinkImage(file) {
    var url = URL.createObjectURL(file);
    try {
      var img = new Image();
      await new Promise(function (resolve, reject) {
        img.onload = resolve;
        img.onerror = function () { reject(new Error("Image illisible : " + file.name)); };
        img.src = url;
      });
      return toJpeg(img, img.naturalWidth, img.naturalHeight);
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function base64(dataUrl) { return dataUrl.slice(dataUrl.indexOf(",") + 1); }

  g.Media = { framesFromVideo: framesFromVideo, shrinkImage: shrinkImage, base64: base64 };
})(window);
