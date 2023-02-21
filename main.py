# https://github.com/69Jesse/Python-Image-Mosaics/
from pathlib import Path
from PIL import Image
import numpy as np
import time
import re

from typing import (
    Generator,
    TypeAlias,
    overload,
    Literal,
)


GRID_SIZE: int = 1024
CELL_SIZE: int = 16
assert GRID_SIZE % CELL_SIZE == 0, f'{GRID_SIZE=} must be divisible by {CELL_SIZE=}'


Color: TypeAlias = tuple[int, int, int]
class Cell:
    average: Color
    def __init__(self, image: Image.Image) -> None:
        self.image: Image.Image = image

    def set_average_color(self) -> None:
        self.average: Color = tuple(map(int, np.array(self.image).mean(axis=(0, 1))))

    def __repr__(self) -> str:
        return f'<Cell({self.image.size[0]}x{self.image.size[1]}, avg={self.average})>'


class Grid:
    def __init__(self, pixelator: 'Pixelator', image: Image.Image, name: str) -> None:
        self.pixelator = pixelator
        self.image: Image.Image = image
        self.dimensions: tuple[int, int] = (self.image.size[0] // CELL_SIZE, self.image.size[1] // CELL_SIZE)
        assert all(d * CELL_SIZE == s for d, s in zip(self.dimensions, self.image.size)), f'{self.image.size=} must be divisible by {CELL_SIZE=}'  # should never raise
        self.name: str = name

    def pixelate(self, cells: list[Cell]) -> None:
        """
        Huge thanks to ConfusedReptile#6830 on the Python Discord for helping me with this.

        It creates a pallette with the average colors of the cells,
        then quantizes the image with that pallette. Then all you
        have to do is go over each pixel and replace it with the
        cell that has the same average color as the pixel.
        """
        colors = [cell.average for cell in cells]
        assert len(colors) <= 256, f'{len(colors)=} must be less than 256'  # should never raise

        pallette = Image.new('P', size=(1, 1))
        pallette.putpalette(c for color in colors for c in color)
        array = np.asarray(self.image.resize(self.dimensions).quantize(
            colors=len(colors),
            method=Image.Quantize.LIBIMAGEQUANT.value,
            palette=pallette,
            dither=Image.Dither.NONE,
        ).convert('RGB'))

        for x in range(self.dimensions[0]):
            for y in range(self.dimensions[1]):
                color: Color = tuple(array[y][x])
                cell = self.pixelator.color_to_cell[color]
                self.image.paste(im=cell.image, box=(x * CELL_SIZE, y * CELL_SIZE))

    def save(self, fp: str) -> str:
        name, _, ext = self.name.rpartition('.')
        fp = f'{fp}/{name} {int(time.time())}.{ext}'
        self.image.save(fp=fp)
        return fp

    def __repr__(self) -> str:
        return f'<Grid({self.image.size[0]}x{self.image.size[1]}, cells={(self.image.size[0]*self.image.size[1]) // CELL_SIZE**2})>'


class Pixelator:
    cells: list[Cell]
    color_to_cell: dict[Color, Cell]
    def __init__(self) -> None:
        self.average_to_best: dict[Color, Cell] = {}

    def image_paths(self, fp: str) -> Generator[Path, None, None]:
        for path in Path(fp).iterdir():
            if path.is_file() and re.match(r'.*\.(png|jpeg|jpg)$', path.name):
                yield path

    @overload
    def get_images(self, fp: str, max_size: int, include_names: Literal[False], ensure_square: bool) -> Generator[Image.Image, None, None]:
        ...

    @overload
    def get_images(self, fp: str, max_size: int, include_names: Literal[True], ensure_square: bool) -> Generator[tuple[Image.Image, str], None, None]:
        ...

    def get_images(self, fp: str, max_size: int, include_names: bool, ensure_square: bool) -> Generator[Image.Image | tuple[Image.Image, str], None, None]:
        for path in self.image_paths(fp=fp):
            image = Image.open(path).convert('RGB')
            ratio = max_size / max(image.size)
            image = image.resize(
                tuple(int(image.size[i] * ratio // CELL_SIZE * CELL_SIZE) for i in range(2)) if not ensure_square else (max_size, max_size),
            )
            yield (image, path.name) if include_names else image

    def setup_cells(self, fp: str) -> None:
        self.cells = []
        self.color_to_cell = {}
        for image in self.get_images(fp=fp, max_size=CELL_SIZE, include_names=False, ensure_square=True):
            cell = Cell(image=image)
            cell.set_average_color()
            if cell.average not in self.color_to_cell:
                if len(self.color_to_cell) == 256:
                    print('Warning: found more than 256 cells, ignoring the rest.')
                    break
                self.cells.append(cell)
                self.color_to_cell[cell.average] = cell
            else:
                print(f'Duplicate color found {cell.average}, ignoring cell.')

    def get_grids(self, fp: str) -> Generator[Grid, None, None]:
        for image, name in self.get_images(fp=fp, max_size=GRID_SIZE, include_names=True, ensure_square=False):
            grid = Grid(pixelator=self, image=image, name=name)
            yield grid


def main() -> None:
    cells_fp: str = './mosaics'
    grids_fp: str = './input'
    output_fp: str = './output'

    pixelator = Pixelator()
    print('Loading cells', end='\r')
    pixelator.setup_cells(fp=cells_fp)
    print(f'Loaded {len(pixelator.cells)} cell{"s"*(len(pixelator.cells) != 1)}')
    count = len(list(pixelator.image_paths(fp=grids_fp)))
    print(f'Found {count} image{"s"*(count != 1)}')

    start = time.time()
    for i, grid in enumerate(pixelator.get_grids(fp=grids_fp), start=1):
        print(f'Processing image {i}/{count} ({grid.name})', end='\r')
        grid.pixelate(cells=pixelator.cells)
        fp = grid.save(fp=output_fp)
        print(f'Successfully saved image {i}/{count} (in {time.time()-start:.2f}s): {fp} ({grid.image.size[0]}x{grid.image.size[1]})')
        start = time.time()


if __name__ == '__main__':
    main()
