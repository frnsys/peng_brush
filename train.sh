#!/bin/bash

NAME=$1

cd pix2pix-tensorflow
python pix2pix.py \
  --mode train \
  --output_dir "../data/$NAME/model" \
  --max_epochs 50 \
  --input_dir "../data/$NAME/train" \
  --which_direction AtoB
  # --checkpoint "../data/$NAME/model"