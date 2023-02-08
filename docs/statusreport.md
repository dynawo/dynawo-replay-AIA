
## Original project description

This task originates in RTE’s need for doing large-scale dynamic simulations while not having to store the states of too many variables (i.e., what we commonly call the “curves”). Therefore, one would like to have a system that, having as input only a relatively small number of curves coming from a dynamic simulation, is able to: - For any given missing variable, approximately reconstruct its whole curve - At any given instant of simulation time, approximately reconstruct the values of all network variables, or at least a substantial subset of all variables (i.e., obtaining a network snapshot at a sufficient level of detail). The aim in these two use cases is to avoid having to redo the full dynamic simulation again.

These goals will be prioritized as follows:
    1. Reconstruct the whole curve:
        a. First for internal generator variables
        b. Then extend it to any kind of injection
        c. Then explore how to do the same for any kind of variable
    2. Reconstruct all values (or a subset) at an instant of time

Note that this problem will probably have to be approached by looking at the inverse optimization problem: which reduced set of curves is the one that is best to store, so that future reconstruction work best? There will certainly be a trade-off in quality vs. storage that is most interesting to analyze and see how it manifests in practice.

Estimated efforts: 1 FTE for 6 months, plus 10% overhead effort for Project Management. An optional extension for another 3.3 MM (along 3 months) is also contemplated.

## Current project scope and status
 
While the project started with the intent to reconstruct any variable in the circuit, after discussion with RTE it has veered towards reconstructing only variables from generators. This is because Dynawo already has the replay functionality with the InfiniteBusFromTable model, which reads the U and UPhase values at the POC from a table. The chosen approach, named DynawoReplay, obtains the desired curves by re-simulating only the target generator connected to an infinite bus. For more information about the explored approaches, see [this](https://drive.google.com/file/d/1xs3SbeKIm1LhQxiAICnGD7pQd0l8lxdv/view?usp=share_link) document.

### DynawoReplay processing pipeline

Specifically, DynawoReplay does the following:  
1. Simulate the whole circuit to generate the .log files containing the names of every variable.  
2. Extract from the .log the names of the variables for V_re, V_im and I_re, I_im at the terminal of each generator.  
3. Generate a new .crv with the terminal variables, and run the simulation to obtain the .csv with all the terminal curves.  
4. Print the terminal V and I values, converted to U and UPhase, into a text file in tabular format.  
5. Generate a new .dyd file for each generator in the system, where the generator is connected to an InfiniteBusFromTable which reads from the file created in the previous step.  
7. Generate a new .par holding only the parameters for the generators.  
8. Simulate each generator and output the curves specified in [name]\_replay.crv.  

### Current issues 

As of now, the replay pipeline is implemented and working for several Dynawo examples such as IEEE14 and IEEE57. However, there are several issues:
- The replayed curves do not always match the originals:  
    - In systems with multiple generators, the difference can be considerable in some instances.   
    - For single-generator-systems (Kundur), the differences are fairly small.   
    - For the TestCase3 system from the Dynawo non-regression tests, the replay matches the original.    
- The replay fails for IEEE14 when the solver parameters are the same as in the original example. Using the IDA parameters from TestCase3 works.  
- The large case tFin cannot be run as it has reference initialization parameters in the .par whose value cannot be deducted from the .dyd file. In this case, it is necessary to have Dynawo calculate these init values and then save them to the .par file.  
- The large case generates very large .csv files, at around 3GB. It is possible that the table for the terminal U, UPhase values is also very large. Moreover, the .crv, .par and .dyd are also much larger than in normal cases and thus processing them requires more time.  

## Pending tasks

- Understand why there's a difference between the original curves and the replayed ones.  
- Understand why the simulation time for the whole circuit and a single generator is the same.  
- Try to replay the large case. This requires:  
    - Getting initialization values in .par from the Dynawo dump instead of the .iidm file.  
    - Optimizing the scripts that generate the .crv file, and the list of terminals and states.  
    - Compressing the table that inputs to the infinite bus.  
- Fix replay not working for some cases, eg IEEE14, when the original solver parameters are used.  

## Source code

The code is split across two repositories:

- [DynawoReplay](https://github.com/grupoaia/DynawoReplay) : replay of generator curves.
- [dynawo-curve-reconstruction](https://github.com/grupoaia/dynawo-curve-reconstruction) : "fake solver" implemented as a new Dynawo class.

Both repositories contain instructions on how to run the code.

The development has been conducted in gimenezp@falcon.grupoaia.es:/home/gimenezp, which contains code from the above two repositories.

## Follow-up meetings

[This Drive folder](https://drive.google.com/drive/folders/1M68HPQziKAFSQeRleMDKweewrCfhsGMS?usp=sharing) contains the slides and documents created for discussion with RTE and internally.



