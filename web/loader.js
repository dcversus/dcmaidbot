export async function loadWorld() {
    const res = await fetch('/world.json');
    return res.json();
}
export async function loadMeta(floorId, locId) {
    const res = await fetch(`/output/floors/${floorId}/${locId}/map.meta.json`);
    return res.json();
}
export async function loadImage(url) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = reject;
        img.src = url;
    });
}
