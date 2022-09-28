import numpy as np
import itertools


def mat_from_mask(mask):
    X, Y = mask.get_size()
    mask_mat = np.zeros([X, Y])
    for x,y in itertools.product(range(X), range(Y)):
        mask_mat[x, y] = np.mean(mask.get_at([x, y]))

    return mask_mat


def text_wrap(surf, text, font, pos=(0, 0), text_color=(0, 0, 0), bgcolor=None, align_center=True, boundary=(0, 0)):
    font.origin = True
    words = [word.split(' ') for word in text.splitlines()]
    width, height = surf.get_size()
    line_spacing = font.get_sized_height() + 2
    x, y = pos
    default_space_width = font.get_rect(' ').width
    for line in words:
        if align_center and len(line) > 1:
            concat_line_rect = font.get_rect(''.join(line))
            space_width = (width - concat_line_rect.width - concat_line_rect.x - x - boundary[0]) // (len(line) - 1)
            space_width = np.maximum(default_space_width, space_width)
        else:
            space_width = default_space_width

        for word in line:
            bounds = font.get_rect(word)
            if x + bounds.width + bounds.x >= width:
                raise ValueError("text too wide for the surface")
            if y + bounds.height - bounds.y >= height:
                raise ValueError("too many text lines for the surface")
            font.render_to(surf, (x, y), word, text_color, bgcolor=bgcolor)
            x += bounds.x + bounds.width + space_width

        x = pos[0]  # Reset the x.
        y += line_spacing  # Start on new row.
    return x, y
