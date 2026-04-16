import imageCompression from "browser-image-compression";

const DEFAULT_OPTIONS = {
  maxSizeMB: 1,
  maxWidthOrHeight: 1280,
  useWebWorker: true,
  fileType: "image/jpeg",
  initialQuality: 0.8
};

export async function compressImageFile(file, overrides = {}) {
  if (!file || !file.type || !file.type.startsWith("image/")) {
    return file;
  }
  try {
    const compressed = await imageCompression(file, { ...DEFAULT_OPTIONS, ...overrides });
    const name = file.name.replace(/\.[^.]+$/, "") + ".jpg";
    return new File([compressed], name, { type: "image/jpeg" });
  } catch (err) {
    console.warn("Image compression failed, sending original:", err);
    return file;
  }
}
