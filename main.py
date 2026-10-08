import maze

def main():
    mz = maze.gen_main_path(maze.Pos(5, 5), 10)
    maze.pretty_print(mz)

if __name__ == "__main__":
    main()