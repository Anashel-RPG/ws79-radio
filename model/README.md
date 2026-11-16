# The Blender model

`ws79_model.blend` is the model the renders in `images/` come from. It was saved with Blender 5.2 LTS.

- One scene with one collection, `WS79`, which holds the radio and its hand microphone as 130 objects.
- Every part hangs from an empty named `ws79_root`, placed at the centre of the base with the feet on the ground.
  Move or turn that empty to place the whole radio.
- Units are metres. The front faces -Y.
- The three textures are packed in the file: the screen, the meters' dial and the walnut of the sides.
- The file holds the model only. It has no camera, no lights and no world, so add your own to render it.

The model shows the finished design: two bar screens, two meters and the microphone. Version 1.0 of the build runs
one screen, the keypad and the speaker.

The pictures in `images/renders/` are renders of this model: the radio from the front, from the side and from the
back, and four close-ups. The front view with its seven numbered marks is the same render with the marks drawn over
it. The case files in `print/` are exported from the same model, so the face in the model has the same openings and
the same pocket as the print file.
