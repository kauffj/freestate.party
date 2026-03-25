/**
 * Shared video player — finds elements by data attributes:
 *   [data-video-player]  → the <video> element
 *   [data-video-play]    → the play button/overlay
 */
(function () {
    var video = document.querySelector('[data-video-player]');
    var playBtn = document.querySelector('[data-video-play]');
    if (!video || !playBtn) return;

    playBtn.addEventListener('click', function () {
        playBtn.classList.add('hidden');
        video.controls = true;
        video.play().catch(function () {
            playBtn.classList.remove('hidden');
            video.controls = false;
        });
    });

    video.addEventListener('ended', function () {
        playBtn.classList.remove('hidden');
        video.controls = false;
    });

    video.addEventListener('error', function () {
        playBtn.innerHTML = '<span class="text-gray-400 text-sm">Video unavailable</span>';
    });
})();
