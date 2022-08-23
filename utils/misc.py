import numpy as np

def text_wrap(surf, text, font, pos=(0, 0), text_color=(0, 0, 0), bgcolor=None, align_center=True):
    font.origin = True
    words = [word.split(' ') for word in text.splitlines()]
    width, height = surf.get_size()
    line_spacing = font.get_sized_height() + 2
    x, y = pos
    space_width = font.get_rect(' ').width
    for line in words:
        if align_center:
            concat_line_rect = font.get_rect(''.join(line))
            space_width = np.maximum(space_width,
                                     np.floor((width - concat_line_rect.width - concat_line_rect.x) / len(line)))

        for word in line:
            bounds = font.get_rect(word)
            if x + bounds.width + bounds.x >= width:
                raise ValueError("text too wide for the surface")
            if y + bounds.height - bounds.y >= height:
                raise ValueError("too many text lines for the surface")
            font.render_to(surf, (x, y), word, text_color, bgcolor=bgcolor)
            x += bounds.width + space_width

        x = pos[0]  # Reset the x.
        y += line_spacing  # Start on new row.
    return x, y
