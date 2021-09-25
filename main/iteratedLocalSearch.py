import xlsxwriter
from techTree import *
import argparse
import logging
import sys
import datetime
from buildOrder import *
from copy import deepcopy

#Algoritmo de búsqueda local iterada
def iteratedLocalSearch(techTree, entityId, entityQty, maxTime, perturbations, iterations, iterationsILS, exportXls):
    #Se obtiene una orden de construcción aleatoria y se aplica una busqueda local
    buildOrder = getRandomBuildOrder(techTree, entityId, entityQty, maxTime)
    bestSolution = greedy(techTree, deepcopy(buildOrder), entityId, entityQty, maxTime, perturbations, iterations)
    bestScore = scoreBuildOrder(techTree, deepcopy(bestSolution), entityId, entityQty, maxTime, 0)
    genScores = [["Generación", "Puntaje"]]
    iteration = 1
    progress = 0
    cls()
    print("Calculando, por favor espere...")
    print("Progreso: ", progress, "%")
    #En cada iteración se perturba la solución inicial y se aplica otra búsqueda local
    while(iteration <= iterationsILS):
        cls()
        print("Calculando, por favor espere...")
        print("Progreso: ", progress, "%")
        perturbatedSolution = perturbationFunction(deepcopy(bestSolution), techTree, entityId, entityQty, maxTime)
        localSolution = greedy(techTree, deepcopy(perturbatedSolution), entityId, entityQty, maxTime, perturbations, iterations)
        score = scoreBuildOrder(techTree, deepcopy(localSolution), entityId, entityQty, maxTime, bestSolution[-1][0])
        genScores.append([iteration, score[-1]])
        #Si el puntaje es mejor, se considera que la solución local es la solución inicial
        if(score[-1] > bestScore[-1]):
            bestSolution = []
            bestSolution = deepcopy(localSolution)
            bestScore = score
        progress = (iteration/iterationsILS)*100
        iteration+=1

    result = [deepcopy(bestSolution), bestScore]

    cls()
    print("- Completado -")
    if(exportXls == 1):
        with xlsxwriter.Workbook('results/Generations_Scores.xlsx') as workbook:
            worksheet = workbook.add_worksheet()

            for row_num, data in enumerate(genScores):
                worksheet.write_row(row_num, 0, data)
        
        cleanResult = [["Time", "Entity", "Supply Occupied", "Total Supply", "Minerals", "Vespene", "Chronoboost"]]
        for row in result[0]:
            cleanResult.append([str(datetime.timedelta(seconds=row[0])), row[1], row[2], row[3], row[4], row[5], row[10]])

        with xlsxwriter.Workbook('results/Build_Order.xlsx') as workbook:
            worksheet = workbook.add_worksheet()

            for row_num, data in enumerate(cleanResult):
                worksheet.write_row(row_num, 0, data)
        
        entitiesBuilt = deepcopy(result[0][-1][7])
        with xlsxwriter.Workbook('results/Entities_Built.xlsx') as workbook:
            worksheet = workbook.add_worksheet()

            for row_num, data in enumerate(entitiesBuilt):
                worksheet.write_row(row_num, 0, data)
        
        unitQueue = deepcopy(result[0][-1][8])
        resultUnitQueue = [["building", "units being built", "time left"]]
        for building in unitQueue:
            resultUnitQueue.append([building[0], ', '.join([str(item) for item in building[1]]), ',  '.join([str(item) for item in building[2]])])
        
        with xlsxwriter.Workbook('results/Unit_Queue.xlsx') as workbook:
            worksheet = workbook.add_worksheet()

            for row_num, data in enumerate(resultUnitQueue):
                worksheet.write_row(row_num, 0, data)

        archonQueue = deepcopy(result[0][-1][9])
        resultArchonQueue = [["Archon", "Qty", "Time left"]]
        for archon in archonQueue:
            resultArchonQueue.append([archon[0], archon[1], archon[2]])
        with xlsxwriter.Workbook('results/Archon_Queue.xlsx') as workbook:
            worksheet = workbook.add_worksheet()

            for row_num, data in enumerate(resultArchonQueue):
                worksheet.write_row(row_num, 0, data)

    return result

#Algoritmo Greedy, genera una solución después de muchas perturbaciones e iteraciones.
def greedy(techTree, buildOrder, entityId, entityQty, maxTime, perturbations, iterations):
    bestSolution = deepcopy(buildOrder)
    bestScore = scoreBuildOrder(techTree, buildOrder, entityId, entityQty, maxTime, 0)
    iteration = 1
    while(iteration <= iterations):
        minTimeOfGen = 0
        maxTimeOfGen = 0
        perturbation = 1
        perturbedSolutions = []
        while(perturbation <= perturbations):
            perturbedSolution = perturbationFunction(deepcopy(bestSolution), techTree, entityId, entityQty, minTimeOfGen)
            perturbedSolutions.append(perturbedSolution)
            if(minTimeOfGen == 0):
                minTimeOfGen = perturbedSolution[-1][0]
            elif(minTimeOfGen > perturbedSolution[-1][0]):
                minTimeOfGen = perturbedSolution[-1][0]
            if(perturbedSolution[-1][0] > maxTimeOfGen):
                maxTimeOfGen = perturbedSolution[-1][0]
            perturbation+=1
        for solution in perturbedSolutions:
            newScore = scoreBuildOrderIterated(techTree, deepcopy(solution), entityId, entityQty, maxTimeOfGen, minTimeOfGen, bestSolution[-1][0])
            if(newScore[-1] > bestScore[-1]):
                bestScore = newScore
                bestSolution = deepcopy(solution)
        iteration+=1
    return bestSolution

#Esta función la ejecuta IRACE para paremetrizar los algoritmos de búsqueda local
def main(PERT, ITER, ITERILS, DATFILE):
    techTree = initTechTree()
    entityId = 16
    entityQty = 10
    maxTime = 2000
    solution = iteratedLocalSearch(techTree, entityId, entityQty, maxTime, PERT, ITER, ITERILS, 0)
    score = scoreBuildOrder(techTree, solution, entityId, entityQty, maxTime, 0)
    
    with open(DATFILE, 'w') as f:
	    f.write(str(score[-1]*100))

if __name__ == "__main__":
    # just check if args are ok
    with open('args.txt', 'w') as f:
        f.write(str(sys.argv))

    # loading example arguments
    ap = argparse.ArgumentParser(description='Build order optimization using iterated local search')
    ap.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    # 5 args to test values
    ap.add_argument('--pert', dest='pert', type=int, required=True, help='Population size')
    ap.add_argument('--iterils', dest='iterils', type=int, required=True, help='Mutation probability')
    ap.add_argument('--iter', dest='iter', type=int, required=True, help='Crossover probability')
    # 1 arg file name to save and load fo value
    ap.add_argument('--datfile', dest='datfile', type=str, required=True, help='File where it will be save the score (result)')

    args = ap.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    logging.debug(args)
    # call main function passing args
    main(args.pert, args.iter, args.iterils, args.datfile)