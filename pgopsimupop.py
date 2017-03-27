'''
Description
Implements abstract class AGPOperation for simuPop simulations,
as coded by Tiago Antao's sim.py modlule.  See class description.
'''
__filename__ = "pgopsimupop.py"
__date__ = "20160126"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

VERBOSE=False
VERY_VERBOSE=True
VERY_VERY_VERBOSE=False

USE_GUI_MESSAGING=False


#if True, then invokes ncurses debugger
DO_PUDB=False

if DO_PUDB:
	from pudb import set_trace; set_trace()
#end if do pudb

import apgoperation as modop
import pgutilities as pgut
#for the lambda-ignore constant:
import pginputsimupop as pgin
from simuOpt import simuOptions
simuOptions["Quiet"] = True
import simuPOP as sp
import sys
import random
import numpy
import copy
import os


'''
2017_03_26. This mod-level def
to import and the pgguiutilities.PGGUI* classes and 
set a flag so that exeptions and other info during the
simulation will raise a message window, is needed because 
when I tried to make the import of the PGGUI* message
classed the default for this module, then an import
error was raised when I tried to start the main program
(negui.py).  There must be some recursive import problem.
Note that the import works when this module is imported
in a separate process (see pgutilities def 
"do_pgopsimupop_replicate_from_files" )

'''
class PGOpSimuPop( modop.APGOperation ):
	'''
	This class inherits its basic interface from class APGOperation, with its 3
	basic defs "prepareOp", "doOP", and "deliverResults"

	Its motivating role is to be a member object of a PGGuiApp object, and to contain the
	defs that do a simupop simulation and give results back to the gui.

	Should use no GUI classes, but strictly utils or pop-gen calls.

	This object has member two objects, an input object that fetches and prepares the
	data needed for the simuPop run, and an output object that formats and/or delivers
	the results.   These objects are exposed to users via getters.  The defs in these 
	member objects can thus be accessed by gui widgets when an object of this class  
	is used as a member of a PGGuiApp object

	The functionality in the name-mangled (self.__*) defs are from Tiago Anteo's sim.py module in 
	his AgeStructureNe project -- his mod-level variables simply assigned to self.
	'''

	INPUT_ATTRIBUTE_NUMBER_OF_MICROSATS="numMSats"
	INPUT_ATTRIBUTE_NUMBER_OF_SNPS="numSNPs"
	DELIMITER_INDIV_ID=";"
	'''
	2017_02_13. For the restrictedGenerator, the maximum
	number of tries to obtain a pop with and Nb within tolerance
	of a target.
	'''
	MAX_TRIES_AT_NB=100

	def __init__(self, o_input, o_output, b_compress_output=True, 
									b_remove_db_gen_sim_files=False,
									b_write_input_as_config_file=True,
									b_do_gui_messaging=False ):  
		'''
			o_input, a PGInputSimuPop object
			o_output, a PGOutputSimuPop object
			b_compress_output, if set to True
				will compress outputfiles using bz2
			b_remove_db_gen_sim_files, if set to True,
				will remove the output files with the
				indicated extensions.  This was added
				after some testing and noting that
				users most interested in using the genepop
				file output suffered from the many additional
				output files when trying to load genepop files
				for ne-estimation
			b_write_input_as_config_file, if set to false, will 
				skip the step in doOp that writes the current params
				to config file, via the input objects attributes 
				and defs. As for the above flag, this was added
				to prevent writing identical configuration files
				for replicate runs of the simulation, and thus
				reduce the number of output files. 
			b_do_gui_messaging.  This param was added 2017_03_26,
				to allow for message windows to pass exception and
				other info to gui users during the simulations,
				which are run in a python process separate from 
				that of the main program.  We could not leave the
				module-level GUI imports and USE_GUI_MESSAGING
				flag active by default, because the main gui 
				program negui.py throws an import error if this module,
				which is also used by the main interface,
				tries to import the PGGUI* classes.  
		'''

		self.__guiinfo=None
		self.__guierr=None

		if b_do_gui_messaging:
			self.__activate_gui_messaging()
		#end if we are to use gui messaging

		super( PGOpSimuPop, self ).__init__( o_input, o_output )

		self.__lSizes = [0, 0, 0, 0, 0, 0]
		self.__reportOps = [ sp.Stat(popSize=True) ]
		self.__is_prepared=False
		self.__compress_output=b_compress_output
		self.__remove_db_gen_sim_files=b_remove_db_gen_sim_files
		self.__write_input_as_config_file=b_write_input_as_config_file

		#if this object is created in one of multiple
		#python so-called "Processes" objects from class
		#"multiprocessing", all pops in their separate "process"
		#will have identical individuals (same number/genotypes) 
		#unless we reseed the numpy random number generator 
		#for each "process:"
		numpy.random.seed()

		'''
		With introduction of the N0 as 
		calculated by other parameters,
		I chose to keep it unaltered in 
		the input object (see N0 property
		in the PGInputSimuPop class), and
		to accomodate lambda adustments,
		to use this attribute as the 
		N0 accessor in the simulation operations.
		We initiallize to the input object's value:
		'''
		self.__current_N0=self.input.N0

		'''
		2017_02_06, we add these attributes to implement,
		per recent meeting with Robin Waples, the 
		restrictedGenerator def to obtain generations
		whose Nb is within a tolerance of a target
		value.  These are set in
		the def createAge.
		'''
		self.__targetNb=None
		self.__toleranceNb=None
		PGOpSimuPop.VALUE_TO_IGNORE=99999

		self.__file_for_nb_records=open( self.output.basename + "_nb_values_calc_by_gen.csv", 'w' )
		self.__file_for_age_counts=open( self.output.basename + "_age_counts_by_gen.csv", 'w' )

		DEFAULT_AGES=50

		self.__total_ages_for_age_file=DEFAULT_AGES if self.input.ages is None \
																else self.input.ages

		s_header="\t".join( [ "generation" ] \
						+ [ "age" + str( idx ) for idx \
							in range( 1, self.__total_ages_for_age_file + 1 ) ] )

		self.__file_for_age_counts.write( s_header + "\n" )

		'''
		See the call to input.makePerCycleNbAdjustmentList in prepareOp.  This list 
		is used by def __harvest
		'''
		self.__nb_and_census_adjustment_by_cycle=None


		return
	#end __init__

	def __activate_gui_messaging(self):

		'''
		2017_03_26. To be called only when the instance
		is in a new process, not that of the main program.

		These PGGUI* classes, if imported by this mod by
		default, cause an import error, possibly due to 
		recursive imports and/or TKinter threading conflicts.
		However, we can use these classes when this object is 
		run in a new python process -- see the creation of this
		object in pgutilities def do_pgopsimupop_replicate_from_files.
		'''

		from pgguiutilities import PGGUIInfoMessage as guiinfo
		from pgguiutilities import PGGUIErrorMessage as guierr

		self.use_gui_messaging=True
		self.__guiinfo=guiinfo
		self.__guierr=guierr
		return

	#end if use gui messaging


	def prepareOp( self, s_tag_out="" ):
		'''
		2017_03_08.  This call converts the list
		of cycle range and rate entries in the 
		listu attribite nbadjustment into a list
		of per-cycle rate adjustments, used by
		this objects def __harvest.
		'''
		try:
			self.__nb_and_census_adjustment_by_cycle=self.input.makePerCycleNbAdjustmentList()
			self.__createSinglePop()
			self.__createGenome()
			self.__createAge()	
			
			s_basename_without_replicate_number=self.output.basename	
			
			if VERY_VERBOSE==True:
				print( "resetting output basename with tag: " + s_tag_out )
			#end if VERY_VERBOSE

			self.output.basename=s_basename_without_replicate_number + s_tag_out

			self.output.openOut()
			self.output.openErr()
			self.output.openMegaDB()

			self.__createSim()
			self.__is_prepared=True

		except Exception as oex:
			if self.__guierr is not None:
				self.__guierr( None, str( oex ) )
			#end if using gui messaging
			raise oex
		#end try...except

		return
	#end prepareOp

	def doOp( self ):
		try:
			if self.__is_prepared:

				#if client has not indicated otherwise,
				#we write the current param set to
				#write the configutation file on which
				#this run is based:
				if self.__write_input_as_config_file:
					self.output.openConf()
					self.input.writeInputParamsToFileObject( self.output.conf ) 
					self.output.conf.close()
				#end if client wants this run to include
				#a configuration file (if many replicates,
				#this may be set to False for all but first)

				#now we do the sim
				self.__evolveSim()
				self.output.out.close()
				self.output.err.close()
				self.output.megaDB.close()

				#note as of 2016_08_23, we don't compress the config file
				if self.__compress_output:
					s_conf_file=self.output.confname
					self.output.bz2CompressAllFiles( ls_files_to_skip=[  s_conf_file ] )
				#end if compress

				self.__write_genepop_file()

				if self.__remove_db_gen_sim_files:
					#noite that this call removes both compressed
					#and uncompressed versions of these files
					#(see PGOutputSimuPop code and comments)
					for s_extension in [ "sim", "gen", "db" ]:
						self.output.removeOutputFileByExt( s_extension )
					#end for output files *sim, *gen, *db
				#end if we are to remove the non-genepop files (gen, sim, db)
			else:
				raise Exception( "PGOpSimuPop object not prepared to operate (see def prepareOp)." )
			#end  if prepared, do op else exception
		except Exception as oex:
			if self.__guierr is not None:
				self.__guierr( None, str( oex ) )
			#end if using gui messaging
			raise oex
		#end try...except

		return
	#end doOp

	def __write_genepop_file( self ):
		i_num_msats=0
		i_num_snps=0
		
		if hasattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_MICROSATS ):
			i_num_msats=getattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_MICROSATS )
		#end if input has num msats

		if hasattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_SNPS ):
			i_num_snps=getattr( self.input, PGOpSimuPop.INPUT_ATTRIBUTE_NUMBER_OF_SNPS )
		#end if input has number of snps

		i_total_loci=i_num_msats+i_num_snps

		if i_total_loci == 0:
			s_msg= "In %s instance, cannot write genepop file.  MSats and SNPs total zero."  \
					% type( self ).__name__ 
			sys.stderr.write( s_msg + "\n" )
		else:
			#writes all loci values 
			self.output.gen2Genepop( 1, 
					i_total_loci, 
					b_pop_per_gen=True,
					b_do_compress=False,
					f_nbne_ratio=self.input.NbNe )
		#end if no loci reported
	#end __write_genepop_file

	def deliverResults( self ):
		return
	#end deliverResults

	def __createGenome( self ):

		size = self.input.popSize
		numMSats = self.input.numMSats
		numSNPs = self.input.numSNPs

		maxAlleleN = 100
		#print "Mutation model is most probably not correct", numMSats, numSNPs
		loci = (numMSats + numSNPs) * [1]
		initOps = []

		for msat in range(numMSats):
			diri = numpy.random.mtrand.dirichlet([1.0] * self.input.startAlleles)
			if type(diri[0]) == float:
				diriList = diri
			else:
				diriList = list(diri)
			#end if type

			initOps.append(
					sp.InitGenotype(freq=[0.0] * ((maxAlleleN + 1 - 8) // 2) +
					diriList + [0.0] * ((maxAlleleN + 1 - 8) // 2),
					loci=msat))
		#end for msat

		for snp in range(numSNPs):
			freq = 0.5
			initOps.append(
					sp.InitGenotype(
					#Position 0 is coded as 0, not good for genepop
					freq=[0.0, freq, 1 - freq],
					loci=numMSats + snp))
		#end for snp

		preOps = []

		if self.input.mutFreq > 0:
			preOps.append(sp.StepwiseMutator(rates=self.input.mutFreq,
					loci=range(numMSats)))
		#end if mufreq > 0

		self.__loci=loci
		self.__genInitOps=initOps
		self.__genPreOps=preOps

		return
	#end __createGenome

	def __createSinglePop( self ):
		popSize=self.input.popSize
		nLoci=self.input.numMSats + self.input.numSNPs
		startLambda=self.input.startLambda
		lbd=self.input.lbd
		
		ldef_init_sex=[]

		'''
		This 2-cull-method selection for intializing sex ratios
		was added 2017_01_05.  When the user selects
		"equal_sex_ratio" in the interface (PGGuiSimuPop), we 
		initialize always using "maleProp=0.5".  When the user
		chooses the "survivial_rates" option, then the configuration
		file param "maleProb" is accessed (its value also may have been 
		reset in the interface), and the sex ratio is determined using 
		Tiago's original assignment, "maleFreq=input.maleProb".
		'''
		if self.input.cull_method == \
					pgin.PGInputSimuPop.CONST_CULL_METHOD_EQUAL_SEX_RATIOS:
			ldef_init_sex=[sp.InitSex(maleProp=0.5)]
		elif self.input.cull_method == \
					pgin.PGInputSimuPop.CONST_CULL_METHOD_SURVIVIAL_RATES:
			ldef_init_sex=[ sp.InitSex(maleFreq=self.input.maleProb) ]
		else:
			s_msg="In PGOpSimuPop instance, def __createSinglePop, "  \
						+ "there is an unknown value for the cull_method " \
						+ "parameter: " + str( self.input.cull_method ) + "."
			raise Exception( s_msg )
		#end if equal sex ratio else

		initOps=ldef_init_sex 

		if startLambda < pgin.START_LAMBDA_IGNORE:
			preOps = [sp.ResizeSubPops(proportions=(float(lbd), ),
								begin=startLambda)]
		else:
			preOps = []
		#end if lambda < VALUE_NO_LAMBA

		postOps = []

		pop = sp.Population(popSize, ploidy=2, loci=[1] * nLoci,
					chromTypes=[sp.AUTOSOME] * nLoci,
					infoFields=["ind_id", "father_id", "mother_id",
					"age", "breed", "rep_succ",
					"mate", "force_skip"])

		for ind in pop.individuals():
			ind.breed = -1000
		#end for ind in pop

		oExpr = ('"%s/samp/%f/%%d/%%d/smp-%d-%%d-%%d.txt" %% ' +
						'(numIndivs, numLoci, gen, rep)') % (
						 self.input.dataDir, self.input.mutFreq, popSize)
		
		self.__pop=pop
		self.__popInitOps=initOps
		self.__popPreOps=preOps
		self.__popPostOps=postOps
		self.__oExpr=oExpr

		return 
	#end __createSinglePop

	def __createSim( self ):
		self.__sim = sp.Simulator(self.__pop, rep=self.input.reps)
		return 
	#endd __createSim

	def __evolveSim(self):

		sim=self.__sim
		gens=self.input.gens
		mateOp=self.__mateOp
		genInitOps=self.__genInitOps
		genPreOps=self.__genPreOps
		popInitOps=self.__popInitOps
		ageInitOps=self.__ageInitOps
		popPreOps=self.__popPreOps
		agePreOps=self.__agePreOps
		popPostOps=self.__popPostOps
		agePostOps=self.__agePostOps
		reportOps=self.__reportOps
		oExpr=self.__oExpr

		sim.evolve( initOps=genInitOps + popInitOps + ageInitOps,
					preOps=popPreOps + genPreOps + agePreOps,
					postOps=popPostOps + reportOps + agePostOps,
					matingScheme=mateOp,
					gen=gens)

	#end __evolveSim

	def __calcDemo( self, gen, pop ):

		v_return_value=None	
		myAges = []
		for age in range(self.input.ages - 2):
			myAges.append(age + 1)
		#end for age in range

		curr = 0

		for i in pop.individuals():
			if i.age in myAges:
				curr += 1
		#end for i in pop

		#todo apply NB change here!!

		'''
		2017_02_25.  We are now using a harvest rate
		instead of the old input.lbd lambda.  In this
		new scenario, we only adjust the number of newborns
		created if our harvest rate is above 1.0, the only
		case in which our new attribute __lambda_for_newborns
		should be non-None.  See def __make_harvest_list. 

		2017_03_02. We are now applying the newborns increase
		(a "negative" lambda,i.e., harvest rate greater than 1.0)
		in the def, __harvest, and so have deleted code that 
		tests-for and applies the attribute,__lambda_for_newborns.
		'''
		v_return_value = self.__current_N0 + curr

		if VERBOSE:
			print( "in __calcDemo, with args, %s %s %s %s, returning %s "
					% ( "gen: ", str( gen ), "pop", str( pop ), str( v_return_value ) ) )
		#end if verbose

		return v_return_value

	#end __calcDemo

	def __getRandomPos( self, arr ):

		sumVal = sum(arr)
		rnd = random.random()
		acu = 0.0
		v_return_value=None

		for i in range(len(arr)):
			acu += arr[i]
			if acu >= rnd * sumVal:
				 v_return_value=i
				 break
			#end if acu . . .
		#end for i in range...

		return v_return_value
	#end __getRandomPos

	def __litterSkipGenerator( self, pop, subPop ):

		fecms = self.input.fecundityMale
		fecfs = self.input.fecundityFemale

		nextFemales = []
		malesAge = {}
		femalesAge = {}
		availOfs = {}
		gen = pop.dvars().gen
		nLitter = None

		if self.input.litter and self.input.litter[0] < 0:
			nLitter = - self.input.litter[0]
		#end if litter and litter[0] < 0

		for ind in pop.individuals():
			if ind.sex() == 1:  # male
				malesAge.setdefault(int(ind.age), []).append(ind)
			else:
				if nLitter is not None:
					availOfs[ind] = nLitter
				#end if nLitter not none

				diff = int(gen - ind.breed)

				#Thu Jun 23 14:00:42 MDT 2016
				#because we want to represent an emtpy
				#skip list as "None" in the interface
				#we test its value in the input object,
				#considet a skip==None to imply that
				#len( skip ) == 0:
				i_len_skip=0 if self.input.skip is None \
									else len( self.input.skip )
				if diff > i_len_skip:
					available = True
				else:
					prob = random.random() * 100
					assert self.input.skip is not None, \
							"Expecting self.input.skip to be list."
					#print prob, self.input.skip, diff
					if prob > self.input.skip[diff - 1]:
						available = True
					else:
						available = False
					#end if prob > skip else not
				#end if diff > len else not

				#print ind, available

				if available:
					femalesAge.setdefault(int(ind.age), []).append(ind)
				#end if available

			#end if ind.sex() == 1
		#end for ind in pop...

		maleFec = []
		for i in range(len(fecms)):
			maleFec.append(fecms[i] * len(malesAge.get(i + 1, [])))
		#end for i in range...

		femaleFec = []
		for i in range(len(fecfs)):
			if self.input.forceSkip > 0 and random.random() < self.input.forceSkip:
				femaleFec.append(0.0)
			else:
				 femaleFec.append(fecfs[i] * len(femalesAge.get(i + 1, [])))
			#end if forceSkip . . . else
		#end for i in range

		while True:

			female = None

			if len(nextFemales) > 0:
				female = nextFemales.pop()
			#end if len( next....

			while not female:
				age = self.__getRandomPos(femaleFec) + 1
				if len(femalesAge.get(age, [])) > 0:

					female = random.choice(femalesAge[age])

					if nLitter is not None:
						if availOfs[female] == 0:
							female = None
						else:
							availOfs[female] -= 1
						#end if availOfs, else not
					elif self.input.litter:
						lSize = self.__getRandomPos(self.input.litter) + 1
						self.__lSizes[lSize] += 1
						if lSize > 1:
							nextFemales = [female] * (lSize - 1)
						#end if size>1

						femalesAge[age].remove(female)
					#end if nLitter is not nonem elif litter
				#end if len( femalsage . . . 
			#end while not female

			male = None

			if self.input.isMonog:
				if female.mate > -1:
					male = pop.indByID(female.mate)
				#end if female.mate 
			#end if isMonog

			while male is None:
				age = self.__getRandomPos(maleFec) + 1
				if len(malesAge.get(age, [])) > 0:
					male = random.choice(malesAge[age])
				#end if len malesage

				if self.input.isMonog:
					if male.mate > -1:
						male = None
					else:
						male.mate = female.ind_id
					#end if male.mate > -1
				#end if isMonog
			#end while male is None...

			female.breed = gen

			if self.input.isMonog:
				female.mate = male.ind_id
			#end if is monog

			if VERY_VERY_VERBOSE:
				print( "in __litterSkipGenerator, yielding with  " \
						+ "male: %s, female: %s"
						% ( str( male ), str( female ) ) )
			#end if verbose

			yield male, female

		#end while True
	#end __litterSkipGenerator

	def __calcNb( self, pop, pair ):

		
		'''
		2017_03_02 This float tolerance is added
		in order to test the kbar value before using 
		it as a divisor (below).  This to control
		the error messaging when our new __harvest
		def creates a population that causes a 
		zero value for kbar.
		'''
		reltol=1e-90

		fecms = self.input.fecundityMale
		fecfs = self.input.fecundityFemale
		cofs = []

		for ind in pop.individuals():
			if ind.sex() == 1:  # male
				fecs = fecms
				pos = 0
			else:
				pos = 1
				fecs = fecfs
			#end if sex==1 else not
			
			if fecs[int(ind.age) - 1] > 0:
				nofs = len([x for x in pair if x[pos] == ind])
				cofs.append(nofs)
			#end if fecs
		#end for ind in pop

		kbar = 2.0 * self.__current_N0 / len(cofs)
		Vk = numpy.var(cofs)

		assert kbar>reltol, "In PGOpSimuPop instance, def __calcNb, " \
								+ "divisor, kbar, is too close to zero."

		nb = (kbar * len(cofs) - 2) / (kbar - 1 + Vk / kbar)
		#print len(pair), kbar, Vk, (kbar * len(cofs) - 2) / (kbar - 1 + Vk / kbar)
	
		return nb
	#end __calcNb

	def __restrictedGenerator( self, pop, subPop ):

		"""No monogamy, skip or litter"""
		nbOK = False
		nb = None
		attempts = 0

		if VERY_VERBOSE:

			print ( "in __restrictedGenerator with " \
					+ "args, pop: %s, subpop: %s"
							% ( str( pop ), str( subPop ) ) )
		#end if VERBOSE

		while not nbOK:

			pair = []
			gen = self.__litterSkipGenerator(pop, subPop)
			#print 1, pop.dvars().gen, nb


			'''
			2017_02_06
			Now testing with goal of using this generator 
			for all sims.  Need to cast __current_N0 as 
			an int for this arg.
			'''

			for i in range( int( round( self.__current_N0 ) ) ):
				pair.append( gen.next() )
			#end for i in range

			'''
			2017_03_24.  Since this def is now always used
			to get the next gen,  Hence we change the gen 
			number after which we apply our nb test, to the 
			gen post burn in
			'''

			first_gen_to_include = 0 \
					if self.input.startLambda >= PGOpSimuPop.VALUE_TO_IGNORE \
					else self.input.startLambda

			if pop.dvars().gen < first_gen_to_include:
				break
			#end if gen number is larger than our burn-in threshold.

			nb = self.__calcNb(pop, pair)

			'''
			2017_02_06
			After meeting with Robin Waples, we now default
			to using this generator, and have added attributes
			to this PGOpSimuPop object to supply the target Nb
			and its tolerance value (rather than using the
			original input.* attributes (see def createAge
			for the initializatio of these values).
			'''
			#### Remm'd out.  This is from the original code using the original param values:
			#if abs(nb - self.input.Nb_orig_from_pop_section ) <= self.input.NbVar:

			if abs(nb - self.__targetNb ) <= self.__toleranceNb:

				'''
				For comparing Nb values as calculated
				(and accepted) on the pops as generated by simuPop, 
				to those created downstream by NeEstimator.
				'''

				s_thisNb=str( nb )
				s_thisgen=str( pop.dvars().gen ) 
				self.__file_for_nb_records.write( \
						"\t".join( [ s_thisgen, s_thisNb ] ) \
						+ "\n" )

				nbOK = True
			else:
				for male, female in pair:
					female.breed -= 1
				#end for male, female

				attempts += 1

			#end for abs( nb ... else not

			if attempts > PGOpSimuPop.MAX_TRIES_AT_NB:
				s_msg="In PGOpSimuPop instance, " \
							+ "def __restrictedGenerator, " \
							+ "for generation, " + str( pop.dvars().gen ) \
							+ ", after " + str( PGOpSimuPop.MAX_TRIES_AT_NB ) \
							+ " tries, the simulation did not generate a " \
							+ "population with an Nb value inside " \
							+ "the tolerance.  Target Nb: " \
							+ str( self.__targetNb ) \
							+ ", and tolerance at +/- " \
							+ str( self.__toleranceNb ) + "."
				#If we are using gui messaging, 
				#we need to show this here, otherwise,
				#because SimuPop is calling this def,
				#the exception won't propogate to
				#doOp, where other exceptions will
				#be shown.
				if self.__guierr is not None:					
					self.__guierr( None, s_msg )
				#end if using gui messaging

				raise Exception( s_msg )

				##### Remm'd out. 
				#We are now using the above exception instead 
				#of this message.  
				#print( "out", pop.dvars().gen )
				#sys.exit(-1)

			#end if attempts > 100

		#end while not nbOK

		for male, female in pair:
			yield male, female
		#end for male, female
	#end __restrictedGenerator

	def __fitnessGenerator( self, pop, subPop ):

		fecms = self.input.fecundityMale
		fecfs = self.input.fecundityFemale

		totFecMales = 0.0
		totFecFemales = 0.0
		availableFemales = []
		perAgeMaleNorm = {}
		perAgeFemaleNorm = {}
		gen = pop.dvars().gen
		ageCntMale = {}
		ageCntFemale = {}

		for ind in pop.individuals():
			if ind.sex() == 1:  # male
				a = self.input.gammaAMale[int(ind.age) - 1]
				b = self.input.gammaBMale[int(ind.age) - 1]
				if a:
					gamma = numpy.random.gamma(a, b)
					ind.rep_succ = gamma
					#ind.rep_succ = numpy.random.poisson(gamma)
				else:
					ind.rep_succ = 1
				#end if a else not

				perAgeMaleNorm[int(ind.age) - 1] = perAgeMaleNorm.get( 
								int(ind.age) - 1, 0.0) + ind.rep_succ

				ageCntMale[int(ind.age) - 1] = ageCntMale.get(
								int(ind.age) - 1, 0.0) + 1
			else:
				#if ind.age == 0: totFecFemales +=0
				a = self.input.gammaAFemale[int(ind.age) - 1]
				b = self.input.gammaBFemale[int(ind.age) - 1]
				if a:
					gamma = numpy.random.gamma(a, b)
					ind.rep_succ = gamma
					#ind.rep_succ = numpy.random.poisson(gamma)
				else:
					ind.rep_succ = 1
				#end if a else not

				perAgeFemaleNorm[int(ind.age) - 1] = perAgeFemaleNorm.get(
								int(ind.age) - 1, 0.0) + ind.rep_succ
				
				ageCntFemale[int(ind.age) - 1] = ageCntFemale.get(
								int(ind.age) - 1, 0.0) + 1

				availableFemales.append(ind.ind_id)
			#end if ind.sex == 1 else not
		#end for ind in pop.individuals

		for ind in pop.individuals():
			if ind.sex() == 1:  # male
				if perAgeMaleNorm[int(ind.age) - 1] == 0.0:
					ind.rep_succ = 0.0
				else:
					ind.rep_succ = ageCntMale[int(ind.age) - 1] * fecms[
								int(ind.age) - 1] * ind.rep_succ / perAgeMaleNorm[
								int(ind.age) - 1]
				#end if perAgeMaleNorm ... else not
				totFecMales += ind.rep_succ
			else:
				if ind.ind_id not in availableFemales:
					continue
				#end if ind,ind_id not ...

				if perAgeFemaleNorm[int(ind.age) - 1] == 0.0:
					ind.rep_succ = 0.0
				else:
					ind.rep_succ = ageCntFemale[int(ind.age) - 1] * fecfs[
								int(ind.age) - 1] * ind.rep_succ / perAgeFemaleNorm[
								int(ind.age) - 1]
				#end if perAgeFemaleNorm ... else not

				totFecFemales += ind.rep_succ
		#end for ind in pop

		nextFemales = []
		while True:

			mVal = random.random() * totFecMales
			fVal = random.random() * totFecFemales
			runMale = 0.0
			runFemale = 0.0
			male = False
			female = False

			if len(nextFemales) > 0:
				female = nextFemales.pop()
				female.breed = gen
			#end iflen( nextFemales ...

			inds = list(pop.individuals())
			random.shuffle(inds)

			for ind in inds:
				if ind.age == 0:
					continue
				#end if ind.age == 0

				if ind.sex() == 1 and not male:  # male
					runMale += ind.rep_succ
					if runMale > mVal:
						male = ind
					#end if runMale

				elif ind.sex() == 2 and not female:
					if ind.ind_id not in availableFemales:
						continue
					#end if ind.ind_id not in avail...

					runFemale += ind.rep_succ

					if runFemale > fVal:
						female = ind
						female.breed = gen
					#end if runFemale
				#end if ind.sex == 1 else ==2 

				if male and female:
					break
				#end if male and female
			#end for ind in inds

			if VERY_VERBOSE:
				s_msg="yielding from __fitnessGenerator with: " \
						+ "%s and %s" \
						% ( str( male ), str( female ) )
				print ( s_msg )
			#end if very verbose

			yield male, female
		#end while True
	#end __fitnessGenerator 

	def __cull( self, pop ):

		kills = []
		for i in pop.individuals():
			if i.age > 0 and i.age < self.input.ages - 1:
				if i.sex() == 1:
					cut = self.input.survivalMale[int(i.age) - 1]
				else:
					cut = self.input.survivalFemale[int(i.age) - 1]
				#end i i.sex==1 else not
				
				if random.random() > cut:
					kills.append(i.ind_id)
				#end if random.random...
			#endif age>0 andage<.....
		#end for i in pop

		pop.removeIndividuals(IDs=kills)

		return True
	#end __cull

	##Brian Trethewey addition for the immediate culling of a proportion of the adult population
	def __equalSexCull(self, pop):

		kills = []
		cohortDict = {}
		for i in pop.individuals():
			indAge = i.age

			if not indAge in cohortDict:
				cohortDict[indAge] = []
			cohortDict[indAge].append(i)


		for cohortKey in cohortDict:
			## !! Cohort 0 does not get culled!!
			if cohortKey == 0.0:
				continue

			cohortKills = []

			#setup data and seperate males and females
			cohort = cohortDict[cohortKey]

			cohortTotal = len(cohort)
			cohortMales = [x for x in cohort if x.sex()==1]
			maleCount = len(cohortMales)
			cohortFemales = [x for x in cohort if x.sex() == 2]
			femaleCount = len(cohortFemales)

			if VERBOSE:
				print(cohortKey)
				print cohortTotal
				print maleCount
				print femaleCount
				print"\n"
			#end if verbose

			#determine survival rate of this cohort
			survivalRate =(self.input.survivalMale[int(cohortKey) - 1]+self.input.survivalFemale[int(cohortKey) - 1])/2
			survivorCount = numpy.round(cohortTotal * survivalRate)
			cullCount = cohortTotal  - survivorCount
			
			if VERBOSE:
				print survivalRate
				print survivorCount
				print cullCount
				print "\n\n"
			#end if verbose

			#choose which sex to kill first
			#flag is one and 0 for easy switching
			killChoiceFlag = round(random.random())
			if femaleCount > maleCount:
				killChoiceFlag = 0
			if maleCount > femaleCount:
				killChoiceFlag = 1

			# halfCull = int(cullCount / 2)
			# maleKills = halfCull
			# femaleKills = halfCull
			# if cullCount%2 ==1:
			# 	if killChoiceFlag == 1:
			# 		maleKills +=1
			# 	else:
			# 		femaleKills+=1
			# maleCulls = random.sample(cohortMales,maleKills)
			# femaleCulls = random.sample(cohortFemales,femaleKills)
			# print len(maleCulls)
			# print len(femaleCulls)
			# for male in maleCulls:
			# 	cohortKills.append(male.ind_id)
			# 	print "male "+str(male.ind_id)
			# for female in femaleCulls:
			# 	cohortKills.append(female.ind_id)
			# 	print "female "+str(female.ind_id)
			# print "\n\n\n"

			#Lottery Loop
			lotteryCount = 0
			maleCullOrder =list(cohortMales)
			femaleCullOrder = list(cohortFemales)
			random.shuffle(maleCullOrder)
			random.shuffle(femaleCullOrder)
			while lotteryCount < cullCount:
				#sample by gender
				if len(maleCullOrder)>len(femaleCullOrder):
					lottoInd = maleCullOrder.pop()
					if VERBOSE:
						print "MaleChosen "+str(lottoInd.ind_id)
					#end if VERBOSE
				else:
					lottoInd = femaleCullOrder.pop()
					if VERBOSE:
						print "FemaleChosen "+str(lottoInd.ind_id)
					#end if VERBOSE
				#if not already "dead"
				if not lottoInd.ind_id in cohortKills:
					lotteryCount +=1
					if VERBOSE:
						print "Dead "+str(lotteryCount)
					#end if VERBOSE

					kills.append(lottoInd.ind_id)
					killChoiceFlag = abs(killChoiceFlag-1)

			#kills.extend(cohortKills)
			# endif age>0 andage<.....
		# end for i in pop
		if VERBOSE:
			print kills
		#end if VERBOSE

		pop.removeIndividuals(IDs=kills)
		return True

	#end __equalSexCull

	def __harvest(self, pop):

		f_reltol=float( 1e-90 )

		gen = pop.dvars().gen

		if VERY_VERBOSE:
			print( "-----------------" )
			print( "in harvest with:" )
			print( "    gen num: " + str( gen ) )
		#end if very verbose

		if self.__nb_and_census_adjustment_by_cycle is None \
					or self.__nb_and_census_adjustment_by_cycle[ gen ] < f_reltol:
			if VERY_VERBOSE:
				print( "leaving harvest without harvesting pop or augmenting N0." )
			#end if very verbose
			return True
		#end if no harvest needed

		if VERY_VERBOSE:
			print ("    current Nb: " + str( self.__targetNb ) )
		#end if very verbose

		#determine harvest rate for this generation
		harvestRate = self.__nb_and_census_adjustment_by_cycle[ gen ]

		#reduce expected NB by 1-harvest rate, except when using an increase-for-newborns,
		#which, though user-entered as a rate > 1.0, is literally a negative harvest rate, 
		#and will proportionally increase the Nb:
		self.__targetNb =self.__targetNb *(1-harvestRate) if harvestRate < 1.0 \
												else self.__targetNb * harvestRate
		
		if VERY_VERBOSE:
			print ("    harvest rate: " + str( harvestRate ) )
		#end if very verbose
	

		'''
		2017_02_26.  No explicit call to a recalc fx is needed.  The assignment 
		of the Nb to the input object, and the subsequent assignment that gets the N0
		from the input object will result in the input object recalculating N0 using its 
		just-updated Nb value, before delivering it to this objects current_N0 attribute.
		'''
		#reduce N0
		# TODO self.__current_N0 = recalcN0(self.__targetNb)
		self.input.Nb=self.__targetNb
		self.__current_N0=self.input.N0

		if VERY_VERBOSE:
			print ("    new targetNb: " + str( self.__targetNb ) )
			print ("    new current N0: " + str( self.__current_N0 ) )
		#end if very verbose

		#If we did the newborn N0 adjustment, we do not harvest.
		if harvestRate >= 1.0:
			if VERY_VERBOSE:
				print ("returning after adjusting newborn N0" )
			#end if very verbose

			return True
		#end if this simulatiuon only adjusts N0 for newborns

		# change rate to correct for nb/bc differenece
#		harvestRate = harvestRate/self.input.NbNc

		kills = []
		cohortDict = {}

		'''
		2017_02_27.  This counter allows
		a check, before culling, that
		the resulting pop size will not be
		zero, which will result in an error condition
		at next call to evolve().  See exception
		test below.
		'''
		i_current_pop_size=0
		for i in pop.individuals():

			i_current_pop_size+=1

			indAge = i.age

			if not indAge in cohortDict:
				cohortDict[indAge] = []
			cohortDict[indAge].append(i)
		#end for each individual
	
		if VERY_VERBOSE:
			print( "    current pop size: " + str( i_current_pop_size ) )
		#end if very verbose

		for cohortKey in cohortDict:
			## !! Cohort 0 does not get culled!!
			# if cohortKey == 0.0:
			#	continue

			cohortKills = []

			# setup data and seperate males and females
			cohort = cohortDict[cohortKey]
			cohortTotal = len(cohort)
			cohortMales = [x for x in cohort if x.sex() == 1]
			maleCount = len(cohortMales)
			cohortFemales = [x for x in cohort if x.sex() == 2]
			femaleCount = len(cohortFemales)

			'''
			2017_02_26. Adding int() because round returns a float,
			which results in a type error in call to random.sample below.
			'''
			maleHarvest = int( numpy.round(maleCount * harvestRate) )
			femaleHarvest = int( numpy.round(femaleCount * harvestRate) )

			if VERY_VERBOSE:
				print ("cohort: " + str( cohortKey ) )
				print ("maleCount: " + str( maleCount ) )
				print ("femaleCount: " + str( femaleCount ) )
				print ("maleHarvest: " + str(maleHarvest) )
				print ("femaleHarvest: " + str(femaleHarvest) )
				print "\n\n"
			#end if very verbose

			# choose which sex to kill first
			# flag is one and 0 for easy switching
			# killChoiceFlag = round(random.random())
			# if femaleCount > maleCount:
			# 	killChoiceFlag = 0
			# if maleCount > femaleCount:
			# 	killChoiceFlag = 1

			'''
			2017_02_26 Correction to the following two lines.  I think numpy.sample is
			supposed to be random.sample
			'''
			#sample  harvest
			maleHarvestList = random.sample(cohortMales,maleHarvest)
			femaleHarvestList = random.sample(cohortFemales,femaleHarvest)

			for ind in maleHarvestList:
#				print "Dead " + str(ind.ind_id)
				kills.append(ind.ind_id)
			for ind in femaleHarvestList:
#				print "Dead " + str(ind.ind_id)
				kills.append(ind.ind_id)

				# kills.extend(cohortKills)
				# endif age>0 andage<.....
		# end for i in pop

		if VERY_VERBOSE:	
			print( "-----------------" )
			print( "in __harvest, removing " \
							+ str( len( kills ) ) \
							+ " individuals " )
		#end if very_verbose

		if len( kills ) == i_current_pop_size: 	
			s_msg="In PGOpSimuPop instance, def __harvest, " \
						+ "Error: harvest will cull the entire " \
						+ "current population."
			raise Exception( s_msg )
		#end if  kill list is entire pop

		pop.removeIndividuals(IDs=kills)
		
		return True
	# end __harvest

	def __zeroC( self, v ):
		a = str(v)
		while len(a) < 3:
			a = "0" + a
		#end while len(a) < 3
		return a
	#end __zeroC

	def __outputAge( self, pop ):
		gen = pop.dvars().gen
		if gen < self.input.startSave:
			return True
		#end if gen < startSave

		rep = pop.dvars().rep

		'''
		Testing age counts per gen
		'''
		totals_by_age={}

		for i in pop.individuals():
			self.output.out.write("%d %d %d %d %d %d %d\n" % (gen, rep, i.ind_id, i.sex(),
								i.father_id, i.mother_id, i.age))

			'''
			As of 2016_08_24:
			Change to Tiago's code to facilitate converting the *gen file 
			(i.e. the file whose handle is output.err), 
			to a genepop file (see def __write_genepop file, 
			we simply write indiv ID and alleles for all individuals
			in this pop to the *gen file, instead of those only for the 
			newborns -- hence we comment out the if statement, and de-indent 
			it's body

			As of 2016_08_31, reverted to the original code, so that
			as before the genepop file will be written with newborns
			only past the first cycle.  This is for the purposes of Congen
			conference, to do Nb estimates on the newborn cohort. Once
			genepop subsampling by individal demographics is implemented,
			we'll once again write the genpop to include all individuals,
			(then do subsampling on the full genepop) but will also include the 
			parentage and age (and other?) info as part of the individual 
			ID (using both the *gen (output.err) and *sim (output.err) files to 
			create the genepop.  It may be that we'll just keep this original 
			filter on the gen, and create the genepop using the indiv list to 
			get the individual ids, and this gen output to lookup genotypes.
			

			As of 2016_09_01, combining the age, sex, and parantage info into the indiv id
			for the first (indiv id) field in the *gen file.  Note above that this info
			is also written to the *sim file.  Putting it in the gen file will allow
			the gen file to be the sole source for writing  gen2genepop conversion
			in instances of type PGOutputSimuPop.  Also, we will again eliminate
			the filter used in writing the gen file indivs/cycle, and to 
			apply age or other filter conditions downstream from this output (using
			instances of class objects in new module genepopindividualid.py). Hence,
			once again we rem out the original filter on age for the gen-file indiv/generation
			'''
#			if i.age == 1 or gen == 0:

			s_id_fields=PGOpSimuPop.DELIMITER_INDIV_ID.join( [ \
						str( i.ind_id ), str( i.sex() ), str( i.father_id ),
						str( i.mother_id ), str( i.age ) ] )

			self.output.err.write("%s %d " % (s_id_fields, gen))

			for pos in range(len(i.genotype(0))):
				a1 = self.__zeroC(i.allele(pos, 0))
				a2 = self.__zeroC(i.allele(pos, 1))
				self.output.err.write(a1 + a2 + " ")
			#end for pos in range

			self.output.err.write("\n")
			
			#end if age == 1 or gen == 0

			'''
			End of change to Tiago's code.
			'''

			'''
			2017_02_07.  We are recording effects on the age 
			structure of using the culls __equalSexCull 
			and __harvest.
			'''
			if int( i.age ) in totals_by_age:
				totals_by_age[ int(i.age) ] += 1
			else:
				totals_by_age[ int( i.age ) ] = 1
			# end if age already recorded, else new age

		#end for i in pop


		'''
		2017_02_07.  To test age structure per gen.
		'''
		ls_entry=[ str( gen ) ]
		
		
		for idx in range( self.__total_ages_for_age_file ):
			i_thisage=idx+1
			if i_thisage in totals_by_age: 
				s_this_val=str( totals_by_age[ i_thisage ]  )
			else:
				s_this_val=str(0)
			#end if age has a total

			ls_entry.append( s_this_val )

		#end for each possible age

		s_entry="\t".join( ls_entry )

		self.__file_for_age_counts.write(  s_entry + "\n" )

		return True
	#end __outputAge

	def __outputMega( self, pop ):
		gen = pop.dvars().gen
		if gen < self.input.startSave:
			return True
		#end if gen < startSave

		for i in pop.individuals():
			if i.age == 0:
				self.output.megaDB.write("%d %d %d %d %d\n" % (gen, i.ind_id, i.sex(),
								i.father_id, i.mother_id))
			#end if age == 0
		#end for i in pop

		return True
	#end __outputMega

	def __setAge( self, pop ):

		probMale = [1.0]

		for sv in self.input.survivalMale:
			probMale.append(probMale[-1] * sv)
		#end for sv in survivalMale

		totMale = sum(probMale)
		probFemale = [1.0]

		for sv in self.input.survivalFemale:
			probFemale.append(probFemale[-1] * sv)
		#end for sv in survivalFemale

		totFemale = sum(probFemale)

		for ind in pop.individuals():
			if ind.sex() == 1:
				prob = probMale
				tot = totMale
			else:
				prob = probFemale
				tot = totFemale
			#end if sex == 1 else not

			cut = tot * random.random()
			acu = 0

			for i in range(len(prob)):

				acu += prob[i]
				if acu > cut:
					age = i
					break
				#end if acu>cut
			#end for i in range

			ind.age = age
		return True
	#end __setAge

	def __createAge( self ):

		pop=self.__pop

		ageInitOps = [
					#InitInfo(lambda: random.randint(0, self.input.ages-2), infoFields='age'),
					sp.IdTagger(),
					#PyOperator(func=self.__outputAge,at=[0]),
					sp.PyOperator(func=self.__setAge, at=[0]),
					]

		agePreOps = [
					sp.InfoExec("age += 1"),
					sp.InfoExec("mate = -1"),
					sp.InfoExec("force_skip = 0"),
					sp.PyOperator(func=self.__outputAge),
					]

		mySubPops = []

		for age in range(self.input.ages - 2):
			mySubPops.append((0, age + 1))
		#end for age in range

		'''
		2017_02_06
		After meeting with Robin Waples, we decided to make the
		Nb-tolerance used in the __restrictedGenerator part of
		all simulations.  To that end we now use the Nb available
		as part of the N0 caluclation, and call the restrictedGenerator.

		We apply our own tolerance value, currently hidden from the user.
		We'll create new attributes for our self object, and intitialize
		a target Nb with the input objects Nb property, with will 
		usually be the Nb used in the N0 caluclation, unless there is no
		"effective size" section in the config file (hence no Nb/Nc and its
		related Nb), so that the only source of an Nb is the "pop" section 
		of the configuration file (see property "Nb" in the PGInputSimuPop 
		object).
		'''

		self.__targetNb=self.input.Nb

		f_nbvar=PGInputSimuPop.DEFAULT_NB_VAR if self.input.NbVar is None \
															else self.input.NbVar 


		self.__toleranceNb=self.__targetNb * f_nbvar

		self.__selected_generator=None

		'''
		Select a generator based on the input parameters,
		and whether we have a target Nb:
		'''
		if( self.input.doNegBinom ):
			self.__selected_generator = self.__fitnessGenerator
		elif self.__targetNb is not None:
			self.__selected_generator = self.__restrictedGenerator
		else:
			self.__selected_generator = self.__litterSkipGenerator 
		#end if we want fitness gen,else restricted, else litter skip

		mateOp = sp.HeteroMating( [ sp.HomoMating(
									sp.PyParentsChooser( self.__selected_generator ),
									sp.OffspringGenerator(numOffspring=1, 
									ops=[ sp.MendelianGenoTransmitter(), sp.IdTagger(),
										sp.PedigreeTagger()],
									sexMode=(sp.PROB_OF_MALES, self.input.maleProb)), weight=1),
									sp.CloneMating(subPops=mySubPops, weight=-1) ],
								subPopSize=self.__calcDemo )


		##### Code Remm'd out
		'''
		2017_02_06
		This is the origial assignment of mateOP before changing the code used to select
		the generator def.
		'''
#		mateOp = sp.HeteroMating( [ 
#					sp.HomoMating(
#					sp.PyParentsChooser(self.__fitnessGenerator if self.input.doNegBinom
#					else (self.__litterSkipGenerator if self.input.Nb_orig_from_pop_section is None else
#					self.__restrictedGenerator)),
#					sp.OffspringGenerator(numOffspring=1, ops=[
#					sp.MendelianGenoTransmitter(), sp.IdTagger(),
#					sp.PedigreeTagger()],
#					sexMode=(sp.PROB_OF_MALES, self.input.maleProb)), weight=1),
#					sp.CloneMating(subPops=mySubPops, weight=-1)],
#					subPopSize=self.__calcDemo )
		##### end temp rem out original

		#Code added 2016_11_01, with new input value "cull_method", we
		#choose our culling def ref accordingly
		def_for_culling=None

		if self.input.cull_method == pgin.PGInputSimuPop.CONST_CULL_METHOD_SURVIVIAL_RATES:
			def_for_culling=self.__cull
		elif self.input.cull_method == pgin.PGInputSimuPop.CONST_CULL_METHOD_EQUAL_SEX_RATIOS:
			def_for_culling=self.__equalSexCull
		else:
			s_msg="In PGOpSimuPop instance, def __createAge, " \
						+ "input object's value for cull_method " \
						+ "is unknown: " + self.input.cull_method \
						+ "."
			raise Exception( s_msg )
		#end if cull method survival rates, equal sex,  else unkown

		#Code revised 2016_11_01 to use the above def_for_culling
		#reference, to assign user-input method:

		##### temp rem out original agePostOps assignment
		'''
		2017_02_07.  We're adding the def __harvest as a post op.

		'''
#		agePostOps = [ sp.PyOperator( func=self.__outputMega ), 
#					sp.PyOperator( func=def_for_culling ) ]
		
		agePostOps = [ sp.PyOperator( func=self.__outputMega ), 
							sp.PyOperator( func=def_for_culling ),
							sp.PyOperator( func=self.__harvest ) ]


		pop.setVirtualSplitter(sp.InfoSplitter(field='age',
			   cutoff=range(1, self.input.ages)))

		self.__ageInitOps=ageInitOps
		self.__agePreOps=agePreOps
		self.__mateOp=mateOp
		self.__agePostOps=agePostOps

		return
	#end __createAge
	
#end class PGOpSimuPop

if __name__ == "__main__":

	try:
		import pginputsimupop as pgin
		import pgoutputsimupop as pgout
		import pgsimupopresources as pgrec
		import pgparamset as pgps
		import pgutilities	 as pgut
	except ImportError as ie:
		s_my_mod_path=os.path.abspath( __file__ )
		sys.path.append( s_my_mod_path )
		import pginputsimupop as pgin
		import pgoutputsimupop as pgout
		import pgsimupopresources as pgrec
		import pgparamset as pgps
		import pgutilities	 as pgut
	#end try to get pgmods

	import time
	import argparse	as ap



	LS_ARGS_SHORT=[ "-l", "-c" , "-p" , "-o"  ]
	LS_ARGS_LONG=[ "--lifetable" , "--configfile", "--paramnamesfile", "--outputbase" ]
	LS_ARGS_HELP=[ "life table file",
						"configuration file",
						"param names file (usually: resources/simupop.param.names)",
						"output files base name" ]

	LS_OPTIONAL_ARGS_SHORT=[ "-s" ]
	LS_OPTIONAL_ARGS_LONG=[ "--paramresets" ]
	LS_OPTIONAL_ARGS_HELP=[ "string, comma-delimted list of param name=value pairs, used to reset paramater values"]

	DELIMIT_RESETS=","
	DELIMIT_NAME_VAL_PAIRS="="
	o_parser=ap.ArgumentParser()

	o_arglist=o_parser.add_argument_group( "args" )

	i_total_nonopt=len( LS_ARGS_SHORT )
	i_total_opt=len( LS_OPTIONAL_ARGS_SHORT )

	for idx in range( i_total_nonopt ):
		o_arglist.add_argument( \
				LS_ARGS_SHORT[ idx ],
				LS_ARGS_LONG[ idx ],
				help=LS_ARGS_HELP[ idx ],
				required=True )
	#end for each required argument

	for idx in range( i_total_opt ):
		o_arglist.add_argument( \
				LS_OPTIONAL_ARGS_SHORT[ idx ],
				LS_OPTIONAL_ARGS_LONG[ idx ],
				help=LS_OPTIONAL_ARGS_HELP[ idx ],
				required=False )
	#end for each required argument

	o_args=o_parser.parse_args()

	s_lifetable_file=o_args.lifetable	
	s_conf_file=o_args.configfile
	s_outbase=o_args.outputbase
	PARAM_NAMES_FILE=o_args.paramnamesfile

	o_param_names=pgps.PGParamSet( PARAM_NAMES_FILE )
	o_resources=pgrec.PGSimuPopResources([ s_lifetable_file ] )
	o_input=pgin.PGInputSimuPop(  s_conf_file, o_resources, o_param_names )
	o_output=pgout.PGOutputSimuPop( s_outbase  )
	
	o_input.makeInputConfig()

	if o_args.paramresets:
		ls_resets=o_args.paramresets.split( DELIMIT_RESETS )
		for s_reset in ls_resets:
			ls_name_val=s_reset.split( DELIMIT_NAME_VAL_PAIRS )
			s_param_name=ls_name_val[ 0 ]
			v_val=eval( ls_name_val[ 1 ] )
			setattr( o_input, s_param_name, v_val )
		#end for each param reset
	#end if caller has param resets

	o_op=PGOpSimuPop( o_input, o_output, b_remove_db_gen_sim_files=True )

	o_op.prepareOp()
	o_op.doOp()
#end if

