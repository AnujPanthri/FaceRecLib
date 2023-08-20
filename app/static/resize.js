async function resize(image_file, max_size = 1000) {
  // Load the image
  // Get as image data
  const imageBitmap = await createImageBitmap(image_file);

  // Resize the image
  var canvas = document.createElement('canvas'),
    width = imageBitmap.width,
    height = imageBitmap.height;
  if (width > height) {
    if (width > max_size) {
      height *= max_size / width;
      width = max_size;
    }
  } else {
    if (height > max_size) {
      width *= max_size / height;
      height = max_size;
    }
  }
  canvas.width = width;
  canvas.height = height;
  canvas.getContext('2d').drawImage(imageBitmap, 0, 0, width, height);

  const blob = await new Promise((resolve) =>
    canvas.toBlob(resolve, 'image/jpeg'),
  );

  // Turn Blob into File
  return new File([blob], image_file.name, {
    type: blob.type,
  });
}
