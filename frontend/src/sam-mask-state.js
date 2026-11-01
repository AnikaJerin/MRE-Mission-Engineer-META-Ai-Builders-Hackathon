export const NO_SAM_MASK_MESSAGE = 'SAM found no matching object in this image. Try a closer crop or a short description of the visible object, then segment again. No mask or measurement was generated.';

export function hasSelectedSamMask(capture, captureId, index = 0) {
  return Boolean(capture && capture.id === captureId &&
    capture.masks?.some(mask => mask.index === index && mask.area_px > 0));
}
