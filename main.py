# -*- coding: utf-8 -*-

import numpy as np
import random
from deap import base, creator, tools
import matplotlib.pyplot as plt
import argparse
import crossover, mutation

positions = None    # 巡回する地点の座標
distances = None    # 地点間の距離
converter = None    # 遺伝子と巡回する順番のコンバータ
current_distance = 0        # 現在の移動距離
current_individual = None   # 現在の遺伝子
order_plot = None       # 巡回ルート表示用のオブジェクト
distance_plot = None    # 距離表示用のオブジェクト
distance_history = []   # 距離の履歴


def evaluate_individual(ind):
    """遺伝子の評価関数。移動距離の合計を返す"""
    total = distances[ind[0], ind[-1]]
    for i, j in zip(ind[:-1], ind[1:]):
        total += distances[ind[i], ind[j]]

    return total,


def create_individual(length):
    """遺伝子を生成する関数"""
    return list(np.random.permutation(length))


def select_individuals(individuals, n, elite_rate):
    """選択関数。指定された割合までエリート選択を行い、残りはルーレット選択を行う"""
    # 適応度順に並び替える
    individuals = sorted(individuals, key=lambda ind: ind.fitness.values[0])
    # エリート選択を行う
    chosen = individuals[:int(n * elite_rate)]   # 選ばれた個体
    rest = individuals[len(chosen):]            # 残りの個体
    # 残りの個体からランキング選択を行う
    sum_inds = sum(map(lambda x: x + 1, range(len(rest))))
    for _ in range(n - len(chosen)):
        sel = np.random.rand() * sum_inds
        for i in range(len(rest)):
            sel -= len(rest) - i
            if sel < 0:
                chosen.append(rest[i])
                break

    return chosen


def print_info_line(gen, min, max, ave, std, is_csv=False):
    """世代の情報を 1 行で表示する関数"""
    if is_csv:
        print(gen, min, max, ave, std, sep=',')
    else:
        print(
            str(gen).ljust(5),
            '{:.4f}'.format(min).rjust(12),
            '{:.4f}'.format(max).rjust(12),
            '{:.4f}'.format(ave).rjust(12),
            '{:.4f}'.format(std).rjust(12))


def update_figure(order_plot, distance_plot):
    """グラフを更新する関数"""
    # 経路を更新
    pos = positions[current_individual + [current_individual[0]]]
    order_plot.set_xdata(pos[:, 0])
    order_plot.set_ydata(pos[:, 1])
    # 距離を更新
    distance_plot.set_xdata(range(len(distance_history)))
    distance_plot.set_ydata(distance_history)


if __name__ == '__main__':
    # argparser
    parser = argparse.ArgumentParser()
    # 位置引数の設定
    parser.add_argument('pos_cnt',   help='Nuber of positions',                  type=int)
    parser.add_argument('gen_cnt',   help='Number of generations',               type=int)
    parser.add_argument('pop_cnt',   help='Number of genes in each generations', type=int)
    parser.add_argument('crossover', help='Rate of crossover (0 ~ 1)',           type=float)
    parser.add_argument('mutation',  help='Rate of individual mutation (0 ~ 1)', type=float)
    parser.add_argument('selection', help='Rate of elite selection (0 ~ 1)',     type=float)
    # オプショナル引数を設定
    parser.add_argument('--seed',       help='Seed value',        type=int)
    parser.add_argument('--verbose',    help='Verbose',           action='store_true')
    parser.add_argument('--csv',        help='Output csv',        action='store_true')
    parser.add_argument('--no-display', help="Don't show graphs", action='store_true')
    # 引数をパース
    args = parser.parse_args()
    # 定数を設定
    POSITIONS_COUNT = args.pos_cnt  # 巡回する地点の数
    GENERATION_COUNT = args.gen_cnt # 計算する世代の数
    INDIVIDUAL_COUNT = args.pop_cnt # 一世代あたりの遺伝子の数
    CROSSOVER_RATE = args.crossover # 交叉率
    MUTATION_RATE = args.mutation   # 突然変異率
    ELITE_RATE = args.selection     # エリート選択率

    # 乱数のシード値を設定
    if args.seed:
        random.seed(args.seed)
        np.random.seed(args.seed)

    # 巡回する地点の座標を作成
    positions = np.random.randint(-1000, 1001, size=(POSITIONS_COUNT, 2))
    # 座標軸ごとの各点の距離を計算
    xs, ys = [positions[:, i] for i in [0, 1]]
    dx = xs - xs.reshape((POSITIONS_COUNT, 1))
    dy = ys - ys.reshape((POSITIONS_COUNT, 1))
    # 各点ごとの距離を計算
    distances = np.sqrt(dx ** 2 + dy ** 2)

    # creator の設定
    creator.create("FitnessMax", base.Fitness, weights=(-1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)
    # toolbox の設定
    toolbox = base.Toolbox()
    toolbox.register("create_individual", create_individual, POSITIONS_COUNT)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.create_individual)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluate_individual)
    toolbox.register("mate", crossover.cycle_crossover)
    toolbox.register("mutate", mutation.inversion_mutation)
    toolbox.register("select", select_individuals, elite_rate=ELITE_RATE)

    # 世代を生成
    pop = toolbox.population(n=INDIVIDUAL_COUNT)

    # 初期世代の各個体の適応度を計算
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
    # 現在の距離と最良の遺伝子を更新
    current_individual = tools.selBest(pop, 1)[0]
    current_distance = evaluate_individual(current_individual)[0]

    # 情報を表示
    if args.verbose:
        print('Positions: {}'.format(POSITIONS_COUNT))
        print('Generations: {}'.format(GENERATION_COUNT))
        print('Individual: {} / generation'.format(INDIVIDUAL_COUNT))
        print('Crossover rate: {}'.format(CROSSOVER_RATE))
        print('Mutation rate: {}'.format(MUTATION_RATE), end='\n\n')
        print()
        print('{0:<5} {1:<12} {2:<12} {3:<12} {4:<12}'.format('Gen', 'Min', 'Max', 'Ave', 'Std'))
        print('=' * 58)
    elif args.csv:
        print('Gen', 'Min', 'Max', 'Ave', 'Std', sep=',')

    # グラフの設定
    if not args.no_display:
        # インタラクティブモードを有効化
        plt.ion()
        # グラフを作成
        fig = plt.figure(figsize=(3, 5))
        ax1 = fig.add_subplot(2, 1, 1)
        ax2 = fig.add_subplot(2, 1, 2)
        # 経路用のグラフを作成
        order_plot, = ax1.plot(positions[:, 0], positions[:, 1], color='blue', linewidth=3, zorder=1)
        # 各地点をプロット
        ax1.scatter(positions[:, 0], positions[:, 1], color='cyan', zorder=2)
        # グラフの範囲を指定
        ax1.set_xlim(-1100, 1100)
        ax1.set_ylim(-1100, 1100)
        # 進捗表示用のグラフを作成
        distance_plot, = ax2.plot([0], [current_distance], color='blue')
        # グラフの範囲を指定
        ax2.set_xlim(0, GENERATION_COUNT)
        ax2.set_ylim(0, current_distance * 1.2)
        update_figure(order_plot, distance_plot)
        plt.draw()
        plt.pause(0.01)

    # 学習
    for g in range(GENERATION_COUNT):
        # 個体を選択し、そのクローンを作成
        offspring = toolbox.select(pop, INDIVIDUAL_COUNT)
        offspring = list(map(toolbox.clone, offspring))

        # シャッフルする
        random.shuffle(offspring)
        # 交叉
        crossover_size = int(len(pop) * CROSSOVER_RATE)  # 交叉する個体数
        for parent1, parent2 in zip(offspring[:crossover_size:2], offspring[1:crossover_size:2]):
            # 交叉により新しい個体を生成し、その個体の適合度をリセットする
            child1, child2 = toolbox.clone(parent1), toolbox.clone(parent2)
            toolbox.mate(child1, child2)
            del child1.fitness.values
            del child2.fitness.values
            # 世代に新しい個体を追加
            offspring.append(child1)
            offspring.append(child2)

        # 突然変異
        for mutant in offspring:
            if np.random.rand() < MUTATION_RATE:
                toolbox.mutate(mutant)
                del mutant.fitness.values


        # 交叉や突然変異で適応度がリセットされた個体を抽出
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        # 適応度を再計算
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # 世代を更新
        pop[:] = offspring
        # 適応度を取得
        fits = [ind.fitness.values[0] for ind in pop]

        # 現在の距離と最良の遺伝子を更新
        current_distance = min(fits)
        current_individual = tools.selBest(pop, 1)[0]
        # 距離の履歴を更新
        distance_history.append(current_distance)

        # 情報を表示
        if args.verbose or args.csv:
            length = len(pop)
            mean = sum(fits) / length
            sum2 = sum([x * x for x in fits])
            std = abs(sum2 / length - mean ** 2) ** 0.5
            print_info_line(g, current_distance, max(fits), mean, std, args.csv)
        # グラフを更新
        if not args.no_display:
            update_figure(order_plot, distance_plot)
            plt.draw()
            plt.pause(0.01)

    # 結果を表示
    if args.verbose:
        print()
        print("Best order:\n  {}".format(current_individual))
        print("Moving distance: {:.4f}".format(current_individual.fitness.values[0]))
