for file in imglib/*; do convert -delay 100 -dispose None $file imglib/000000.jpg -rotate 90 -crop 1024x1200+28+450 +repage -loop 0 ${file%.*}.gif; done

