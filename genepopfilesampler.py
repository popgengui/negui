
'''
Description
Class GenepopFileSampler instances operate on GenepopFileManager objects,
adding subsamples to the GenepopFileManager's subsample collections according,
to one of mulitple sampling schemes.  Class GenepopFileSampleParams give 
values used in sampling.
'''

__filename__ = "genepopfilesampler.py"
__date__ = "20160710"
__author__ = "Ted Cosart<ted.cosart@umontana.edu>"

import random

from genepopindividualid import GenepopIndivCriterion as gic
from genepopindividualid import GenepopIndivIdVals

#mod level helper defs and assignments:

TAG_DELIMITER="_"

SCHEME_NONE="none"
SCHEME_PROPORTION="proportion"
SCHEME_REMOVAL="remove"
SCHEME_CRITERIA="criteria"
SCHEME_COHORTS="cohorts"
SCHEME_COHORTS_PERC="cohortsperc"
SCHEME_RELATEDS="relateds"

#subsampling loci, not individuals
SCHEM_LOCI="loci"

def make_subsample_tag( v_value, i_replicate_number, s_scheme ):
	if s_scheme==SCHEME_NONE:
		s_val_initial="o"
	elif s_scheme==SCHEME_PROPORTION:
		s_val_initial="p"
	elif s_scheme==SCHEME_REMOVAL:
		s_val_initial="n"
	elif s_scheme==SCHEME_CRITERIA:
		s_val_initial="c"
	elif s_scheme==SCHEME_COHORTS:
		s_val_initial="h"
	elif s_scheme==SCHEME_COHORTS_PERC:
		s_val_initial="t"
	elif s_scheme==SCHEME_RELATEDS:
		s_val_initial="r"
	elif s_scheme==SCHEME_LOCI:
		s_val_initial="l"
	else:
		s_msg = "In genpopfilesampler.py, def make_subsample_tag, " \
								+ "scheme, " + s_scheme \
								+ ".  The scheme name is either unknown " \
								+ "or has no associated tag."
		raise Exception( s_msg )
	#end if scheme proportion, else removal, else error

	return TAG_DELIMITER.join( [ s_val_initial, 
									str( v_value ), "r", 
									str( i_replicate_number ) ] )
#end make_subsample_tag

def get_sample_value_and_replicate_number_from_sample_tag( s_sample_tag, s_scheme ):
		
		ls_fields=s_sample_tag.split( TAG_DELIMITER )

		v_sample_value=None	
		if s_scheme==SCHEME_NONE:
			v_sample_value=str( ls_fields[ 1 ] )
		elif s_scheme==SCHEME_PROPORTION:
			v_sample_value=float( ls_fields[ 1 ] )
		elif s_scheme==SCHEME_REMOVAL:
			v_sample_value=int( ls_fields[ 1 ] )
		elif s_scheme==SCHEME_CRITERIA:
			v_sample_value=str( ls_fields[ 1 ] )
		elif s_scheme==SCHEME_COHORTS:
			v_sample_value=str( ls_fields[ 1 ] )
		elif s_scheme==SCHEME_RELATEDS:
			v_sample_value=str( ls_fields[ 1 ] )
		elif s_scheme==SCHEME_COHORTS_PERC:
			v_sample_value=str( ls_fields[ 1 ] )
		else:
			s_msg = "In genpopfilesampler.py, "\
						+ "def get_sample_value_and_replicate_number_from_sample_tag, " \
						+ "scheme," + s_scheme + ".  The name is either uknown or has no " \
						+ "determined parsing format."
			raise Exception( s_msg )
		#end if scheme is proportion, else removal, else error

		i_replicate_number=int( ls_fields[ 3 ] )

		return ( v_sample_value, i_replicate_number )
#end get_sample_value_and_replicate_number_from_sample_tag

class GenepopFileSampler( object ):
	'''
	Class GenepopFileSampler instances operate on GenepopFileManager objects,
	adding subsamples to the GenepopFileManager's subsample according to one of
	mulitple sampling schemes.  It's chief motivation is a need to enccapsulate 
	a session in which a large number of samples need to be taken from a single
	genepop file, according to one of various possible sampling schemes.
	'''


	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		self.__filemanager=o_genepopfilemanager
		self.__sampleparams=o_genepopfilesampleparams
		return
	#end __init__
	
	@property
	def filemanager( self ):
		return self.__filemanager
	#end property filemanager

	@property
	def sampleparams( self ):
		return self.__sampleparams
	#end property sampleparams

	def __doSample( self ):
		return
	#end __do_sampling

#end class GenepopFileSampler

class GenepopFileSampleParams( object ):
	'''
	Supporting objects for GenepopFileSampler instances,
	proving the sampling parameters.  For example, for 
	sampling by proportions, this object would provide
	a list of proportions of which each population is to 
	be sampled, and a number of replicates indicating how
	many samples to take at each proportion.  Further,
	These objects also supply a list of population numbers,
	from the range 1,2,3,...,N of the genepop files N
	populations
	'''
	def __init__( self, li_population_numbers, 
				s_population_subsample_name="population_numbers",
				s_sample_tag=None ):
		'''
		Param li_populations is a list of integers,
		each of i of which refers to the ith population
		in the genepop file as represented by a 
		genepopfilemanager object
		'''
		self.__populationnumbers=li_population_numbers
		self.__populationsubsamplename=s_population_subsample_name
		self.__sample_tag=s_sample_tag
		return
	#end __init__

	@property
	def population_numbers( self ):
		return self.__populationnumbers
	#end property population_numbers

	@property
	def population_subsample_name( self ):
		return self.__populationsubsamplename
	#end property population_subsample_name

	@property
	def sample_tag( self ):
		return self.__sample_tag
	#end property sample_tag

#end  class GenepopFileSampleParams

class GenepopFileSampleParamsLoci( GenepopFileSampleParams ):
	'''
	Parameter set for sampling loci from the ith to the jth, 
	as listed in the genepop file individual entries. 
	Also provides for a max_total_loci, to trunctate the total loci 
	to this number by random sampling. Also provides a propotioin value,
	if needed, for randomly sampling a proportion of the loci within
	the given range.  See classs below, GenepopFileSamplerLociByRangeAndTotal and
	GenepopFileSampleParamsLociByRangeAndPercentage
	'''
	def __init__( self, li_population_numbers, i_min_loci_position,
												i_max_loci_position,
												i_max_total_loci=None,
												f_proportion=None,
												i_replicates=1,
												s_population_subsample_name="population_numbers",
												v_sample_value="rt",
												s_sample_tag=None ):

	
		GenepopFileSampleParams.__init__( self,
							li_population_numbers=li_population_numbers,
							s_population_subsample_name=s_population_subsample_name,
							s_sample_tag=s_sample_tag )			
												
		self.__min_loci_position=i_min_loci_position
		self.__max_loci_position=i_max_loci_position
		self.__max_total_loci=i_max_total_loci
		self.__sample_param_value="rt"
		self.__replicates=i_replicates
		self.__proportion=f_proportion

		return
	#end __init__

	@property
	def min_loci_position( self ):
		return self.__min_loci_position
	#end property min_loci_position

	@property
	def max_loci_position( self ):
		return self.__max_loci_position
	#end property max_loci_position

	@property
	def max_total_loci( self ):
		return self.__max_total_loci
	#end property max_total_loci

	@property
	def replicates( self ):
		return self.__replicates
	#end property replicates

	@property
	def sample_param_value( self ):
		return self.__sample_param_value
	#end property sample_param_value

	@property
	def proportion( self ):
		return self.__proportion
	#end property proportion

#end class GenepopFileSampleParamsLoci

class GenepopFileSampleParamsNone( GenepopFileSampleParams ):
	'''
	No selection of individuals, only a min/max for indiv count
	per population.  If max exceeded, then sampler randomly 
	selectes individuals.
	'''
	def __init__( self, li_population_numbers,
				i_min_pop_size,
				i_max_pop_size, 
				i_replicates=1,
				s_population_subsample_name="population_numbers",
				v_sample_value = "n",
				s_sample_tag=None ):

		GenepopFileSampleParams.__init__( self,
									li_population_numbers=li_population_numbers,
									s_population_subsample_name=s_population_subsample_name,
									s_sample_tag=s_sample_tag )

		self.__min_pop_size=i_min_pop_size
		self.__max_pop_size=i_max_pop_size
		self.__sample_param_value=v_sample_value
		self.__replicates=i_replicates
		
		return
	#end __init__

	@property
	def min_pop_size( self ):
		return self.__min_pop_size
	#end min_pop_size

	@property
	def max_pop_size( self ):
		return self.__max_pop_size
	#end max_pop_size

	@property
	def sample_param_value( self ):
		return self.__sample_param_value
	#end sample_param_value

	@property
	def replicates( self ):
		return self.__replicates
	#end replicates

#end class GenepopFileSampleParamsNone

class GenepopFileSampleParamsProportion( GenepopFileSampleParams ):
	def __init__( self, li_population_numbers, 
			lf_proportions, 
			i_replicates, 
			s_population_subsample_name="population_numbers",
			s_sample_tag=None ):

		'''
		param li_populations, list of ints, which pops to sample (see remarks, parant class )
		param lf_proportions, list of floats, each pop sampled at each of these proportions
		param i_replicates, one integer, each pop sampled at each proportion this many times
		GenepopFileSampleParams.__init__( self, li_populations )
		'''

		GenepopFileSampleParams.__init__(self, li_population_numbers=li_population_numbers, 
											s_population_subsample_name=s_population_subsample_name,
											s_sample_tag=s_sample_tag )
		self.__proportions=lf_proportions
		self.__replicates=i_replicates
		return
	#end __init__

	@property
	def proportions( self ):
		return self.__proportions
	#end property proportions
	
	@property
	def replicates( self ):
		return self.__replicates
	#end property replicates

#end class GenepopFileSampleParamsProportion

class GenepopFileSampleParamsRemoval( GenepopFileSampleParams ):

	'''
	Parameters for sampling scheme such that for each population
	we randomly remove N of the M individuals, removing all M where
	N>=M, repeating i_replicate times. 
	
	When the b_do_all_combos_when_n_equals_one flag in __init__ is
	set to True (the default), we treat N=1 differently, and 
	exhaust all possible removals -- i.e, in each pop_i 
	of size M_i, removing each N where N=1,2,3...M_i.
	'''

	def __init__( self, 
			li_population_numbers,
			li_n_to_remove,
			i_replicates,
			s_population_subsample_name="poplulation_numbers",
			b_do_all_combos_when_n_equals_one=True,
			s_sample_tag=None ):

		'''
		param li_population_numbers, list of ints, see parent class
		param li_n_to_remove, list of ints, indicating, for each pop, randomly 
			  remove n individuals
		param i_replicates, for each i_n, repeat i_replicates times
		param s_population_subsample_name, see parent class
		param b_do_all_combos_when_n_equals_one -- if true treat n=1 differently,
			  by repeating a remove-one-indiv for each indiv in each pop.
		'''

		GenepopFileSampleParams.__init__( self, 
					li_population_numbers=li_population_numbers, 
					s_population_subsample_name=s_population_subsample_name,
					s_sample_tag=s_sample_tag )

		self.__n_to_remove=li_n_to_remove
		self.__replicates=i_replicates
		self.__do_all_combos_when_n_equals_one=b_do_all_combos_when_n_equals_one
		return
	#end __init

	@property
	def n_to_remove( self ):
		return self.__n_to_remove
	#end property n_to_remove

	@property
	def replicates( self ):
		return self.__replicates
	#end property replicates

	@property
	def do_all_combos_when_n_equals_one( self ):
		return self.__do_all_combos_when_n_equals_one
	#end property do_all_combos_when_n_equals_one

#end class GenepopFileSampleParamsRemoval

class GenepopFileSampleParamsCriteria( GenepopFileSampleParams ):

	'''
	Parameters for sampling scheme such that for each population
	we select individuals that meet one or more criteria as 
	given in the individual ID as processed by the classes in
	genepopindividualid.py. 
	'''

	def __init__( self, 
			o_genepop_indiv_id_fields,
			o_genepop_indiv_id_critera,
			li_population_numbers,
			s_population_subsample_name="poplulation_numbers",
			i_replicates=1,
			i_min_sampled_pop_size=None,
			i_max_sampled_pop_size=None,
			s_sample_tag=None ):

		'''
		param o_genepop_indiv_id_fields, instance of GenepopIndivIdFields,
		param do_genepop_indiv_id_critera, dictionary of instances of 
				type GenepopIndivCriterion, keyed to their member
				property, "name: (__criterionname)
		param li_population_numbers, list of pop numbers (in the genepop file)
				to which we apply the critera
		param s_population_subsample_name, see parent class
		param i_replicates will usually be "1", since there should be
				no variation between 2 such samplings of a genepop file.
		param i_max_sampled_pop_size, if not None, is meant to be passed
			to the criteria subsampling def in a GenepopFileManager
			instance (passed by the GenepopFileSampler Instance using this
			class), so that, after all indivs have been chosen by the 
			criteria, the subsample in then reduced (if > i_max_sampled_pop_size),
			by random selection to be equal to i_max_sampled_pop_size.
			If None, then we expect the Samper instance to pass None to 
			the GenepopFileManager instance for the max, and so to ignore
			the restriction.
		'''

		GenepopFileSampleParams.__init__(self, 
					li_population_numbers=li_population_numbers, 
					s_population_subsample_name=s_population_subsample_name,
					s_sample_tag=s_sample_tag )

		self.__fields=o_genepop_indiv_id_fields
		self.__criteria=o_genepop_indiv_id_critera
		self.__replicates=i_replicates
		self.__min_pop_size=i_min_sampled_pop_size
		self.__max_pop_size=i_max_sampled_pop_size

		return
	#end __init

	@property
	def fields( self ):
		return self.__fields
	#end def fields

	@property
	def criteria( self ):
		return self.__criteria
	#end def criteria

	'''
	For conformity with other params 
	objects, we include a replicates property,
	though all replicate seesions of sampling
	the same genepop file by a given set of
	criteria should be identical. So, default
	value as set in __init__ param is "1"
	'''
	@property
	def replicates( self ):
		return self.__replicates
	#end property replicates

	@property
	def min_sampled_pop_size( self ):
		return self.__min_pop_size
	#end property min_sampled_pop_size
	@property
	def max_sampled_pop_size( self ):
		return self.__max_pop_size
	#end property max_sampled_pop_size

#end class GenepopFileSampleParamsCriteria

class GenepopFileSampleParamsCriteriaOnGroups( GenepopFileSampleParamsCriteria ):

	'''
	This class extends GenepopFileSampleParamsCriteria
	by adding a grouping function, whereby individuals
	are subsampled into groups according to whether they
	match a set of one or more field values. Other criteria
	can also be applied.  The member GenepopIndivCriteriaCriteria 
	object can also be None, in which case subsampleing will be
	Parameters for sampling scheme such that for each population
	we select individuals that meet one or more criteria as 
	given in the individual ID as processed by the classes in
	genepopindividualid.py. 
	'''


	def __init__( self, 
				o_genepop_indiv_id_fields,
				o_genepop_indiv_id_critera,
				li_population_numbers,
				ls_field_names_to_group_on,
				s_population_subsample_name="poplulation_numbers",
				i_replicates=1,
				i_max_sampled_pop_size=None,
				s_sample_tag=None ):

		'''
		param o_genepop_indiv_id_fields, instance of GenepopIndivIdFields,
		param do_genepop_indiv_id_critera, dictionary of instances of 
				type GenepopIndivCriterion, keyed to their member
				property, "name: (__criterionname)
		param li_population_numbers, list of pop numbers (in the genepop file)
				to which we apply the critera.
		param ls_field_names_to_group_on, list of strings, field names, 
				on which to group individuals.  These unique sets of
				field values will then be used as criteria in subsampling.
		param s_population_subsample_name, see parent class
		param i_replicates will usually be "1", since there should be
				no variation between 2 such samplings of a genepop file.
		param i_max_sampled_pop_size, if not None, is meant to be passed
			to the criteria subsampling def in a GenepopFileManager
			instance (passed by the GenepopFileSampler Instance using this
			class), so that, after all indivs have been chosen by the 
			criteria, the subsample in then reduced (if > i_max_sampled_pop_size),
			by random selection to be equal to i_max_sampled_pop_size.
			If None, then we expect the Samper instance to pass None to 
			the GenepopFileManager instance for the max, and so to ignore
			the restriction.
		'''

		GenepopFileSampleParamsCriteria.__init__( \
					self, 
					o_genepop_indiv_id_fields,
					o_genepop_indiv_id_critera,
					li_population_numbers=li_population_numbers, 
					s_population_subsample_name=s_population_subsample_name,
					i_replicates=i_replicates, 
					i_max_sampled_pop_size=None,
					s_sample_tag=s_sample_tag )

		
		self.__grouped_fields
		return
	#end __init

	@property
	def grouped_fields( self ):
		return self.__grouped_fields
	#end def fields

#end class GenepopFileSampleParamsCriteriaOnGroups

class GenepopFileSampleParamsAgeStructureCohorts( GenepopFileSampleParams ):

	def __init__( self, o_genepop_indiv_id_fields, 
								li_population_numbers,
								i_max_age,
								i_min_individuals_per_gen,
								i_max_individuals_per_gen, 
								i_ceiling_if_no_total_individuals_per_gen=200,
								#this param added 2016_10_19, to allow
								#subclass of the GenepopFileSamplerIndividualsAgeStructureCohorts 
								#that will sample a proportion of the cohort(s) collected.
								#default None means it is not used, as for the original sampler
								#that used the min/max indiv per gen limits:
								f_proportion=None,
								s_population_subsample_name="population_numbers",
								i_replicates=1,
								b_lp=False,
								s_sample_param_value="c",
								s_sample_tag=None ):

			GenepopFileSampleParams.__init__(self, 
						li_population_numbers=li_population_numbers, 
						s_population_subsample_name=s_population_subsample_name,
						s_sample_tag=s_sample_tag )

			self.__fields=o_genepop_indiv_id_fields	
			self.__max_age=i_max_age
			self.__max_individuals_per_gen=i_max_individuals_per_gen
			self.__min_individuals_per_gen=i_min_individuals_per_gen
			self.__replicates=i_replicates
			self.__lp=b_lp
			#Value used in naming the subsample (see global def, 
			#make_subsample_tag).
			self.__sample_param_value=s_sample_param_value

			#proportion of indivicuals to sample, after
			#even (uniform total per age) sampling.  This 
			#property only employed in the sublcass
			#GenepopFileSamplerIndividualsAgeStructureCohortsPercentage

			self.__proportion=f_proportion

			return
	#end __init__

	@property
	def fields( self ):
		return self.__fields
	#end fields
	@property
	def max_age( self ):
		return self.__max_age
	#end indiv_per_gen

	@property
	def max_indiv_per_gen( self ):
		return self.__max_individuals_per_gen
	#end indiv_per_gen

	@property
	def min_indiv_per_gen( self ):
		return self.__min_individuals_per_gen
	#end indiv_per_gen

	@property
	#This is not used in class 
	#GenepopFileSamplerIndividualsAgeStructureCohorts,
	#It is used in the derived class,
	#GenepopFileSamplerIndividualsAgeStructureCohortsPercentage.
	def proportion( self ):
		return self.__proportion
	#end proportion

	@property
	def replicates( self ):
		return self.__replicates
	#end def replicates

	@property
	def sample_param_value( self ):
		return self.__sample_param_value
	#end def sample_param_value

#end class GenepopFileSampleParamsAgeStructureCohorts

class GenepopFileSamplerIndividualsAgeStructureCohorts( GenepopFileSampler ):
	'''
	This sampler class is meant to implement Tiago's sampling code in his
	sampleIndivsCohort.py module.  It samples  individuals grouped by age.
	The GenepopFileSampleParams object used by instances
	of this class has the values Tiagos module takes at the command line 
	that restrict the total individuals per gen.  His command line params 
	startGen and endGen paramters are already implemented via the Sampler's
	li_population_numbers parameter.
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, 
											o_genepopfilesampleparams )
		return
	#end __init__

	def __get_individuals( self, dli_indiv_index_by_age ):

		'''
		Follows very closely Tiago's def sampleIndivsCohort.getIndivs.
		'''
		li_individuals=[]

		li_lens_indiv=[ len( li_indivs_count ) \
							for li_indivs_count in \
							list( dli_indiv_index_by_age.values() ) ]
	
		if len( li_lens_indiv ) > 0:
			i_max_individuals_per_cohort=min( li_lens_indiv  )
		else:
			i_max_individuals_per_cohort = 0
		#end if we have any indivs in any cohort else no indiv


		for i_age, li_indivs_this_age in list( dli_indiv_index_by_age.items() ):
			li_individuals.extend( random.sample( li_indivs_this_age, 
													i_max_individuals_per_cohort ) )
		#end for each item in dict of indivs by age
		
		return li_individuals

	#end __get_individuals

	def resize_sample_to_meet_size_criteria( self, li_indiv_by_age_collected ):
		'''
		Given the individuals collected by age, 
		check min/max limits and subsample
		if needed.  If within limits, return
		the original list
		'''

		#If too few we raise an error.  If too many we
		#randomly select to reach our max valid pop size
		i_tot_collected=len( li_indiv_by_age_collected )

		li_indiv_by_age_sampled=None

		if i_tot_collected < self.sampleparams.min_indiv_per_gen:
			s_msg="In GenepopFileSamplerIndividualsAgeStructureCohorts instance, " \
					"after sampling cohorts, total collected, " \
					+ str( i_tot_collected ) \
					+ ", is less than the value given for " \
					+ "the minimum pop size, " \
					+ str( self.sampleparams.min_indiv_per_gen ) \
					+ "."
			raise Exception ( s_msg )

		elif i_tot_collected > self.sampleparams.max_indiv_per_gen:
			try:

				li_indiv_by_age_sampled=random.sample( \
									li_indiv_by_age_collected,
									self.sampleparams.max_indiv_per_gen )
										
			except Exception as oex:
				s_sample_error_msg= \
					"In GenepopFileSamplerIndividualsAgeStructureCohorts " \
						+ "instance, def doSample, "  \
						+ "random.sample failed on list of " \
						+ str( len( li_indiv_by_age_collected ) ) \
						+ " individuals.  Target total to be sampled: " \
						+ str( self.sampleparams.max_indiv_per_gen ) + "."
				s_msg=s_sample_error_msg \
						+ "  Exception message: " + str( oex ) + "."
				raise Exception( s_msg )
			#end try . . . except
		else:
			#within interval min to max pop size, so keep original 
			li_indiv_by_age_sampled=li_indiv_by_age_collected

		#end if too few, error, else if too many, sample, else no change
		return li_indiv_by_age_sampled
	#end resize_sample_to_meet_size_criteria 

	def doSample( self ):
		'''
		Sample siblings in age group, for ages < max age. Sample identical numbers per age, 
		then reduce to meet max indiv per gen or proportion.  See Tiagos code in his 
		sampleIndivsCohort.py module.  Note that when param "lp" is included, then
		Tiagos code adds to his lines that print out, gen_number\sindiv, the same lines
		without a gen number, presumably for downstream filtering when making the final
		genenpop file. As of 2016_09_12, the output when the "lp" arg is added, is not 
		implemented.
		'''

		#estimator driver needs a pop number subsample when it adds calls to the NeEstimator:
		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers,
										s_subsample_tag=self.sampleparams.population_subsample_name )

		FIELD_NAME_AGE="age"

		dli_indiv_index_lists_by_pop_number={}
		
		i_replicate_count=self.sampleparams.replicates

		for i_replicate_number in range( i_replicate_count ):

			for i_pop_number in self.sampleparams.population_numbers:

				ls_id_list=self.filemanager.getListIndividuals( i_pop_number )

				'''
				We assume that the list of Id's in the individual list
				is indexed such that the zeroth id corresponds to the first
				indiv as ordered in the genepop file, the [1] indexed id
				is the second indiv, etc.
				'''
				i_tot_indiv=len( ls_id_list )

				dli_indiv_index_by_age={}
				
				for idx in range( i_tot_indiv ):

					s_id=ls_id_list[ idx ]

					o_id_vals=GenepopIndivIdVals( s_id, 
										self.sampleparams.fields )
					
					#age may be float or int:
					v_age=o_id_vals.getVal( FIELD_NAME_AGE )

					if v_age > self.sampleparams.max_age:
						continue
					#end if too old, continue

					'''
					Note that idx+1 gives the number of the individual as ordered by its
					entry in the "pop" section of this pop in the genepop file, as used
					by the genepopfilemanager object to point to it's byte address in the file.
					Thus it's our way of collecting samples of individuals and passing them into the
					genepop file manager object's subsampling records (its attribute 
					__indiv_subsamples).
					'''

					i_indiv_number=idx+1

					dli_indiv_index_by_age.setdefault( \
								v_age, [] ).append( i_indiv_number ) 

				#end for each individual's id	

				li_indiv_by_age_collected=self.__get_individuals( \
												dli_indiv_index_by_age ) 
			
				'''
				Resize the sample if it exceeds size limits (as given by
				min,max, or, in the case of a proportionaly sampling scheme
				(subclass GenepopFileSamplerIndividualsAgeStructureCohortsPercentage),
				subsample a proportion.  Note that these lists will be sorted by the
				GenepopFileManager in the subsampleIndividualsByNumberList call
				below.
				'''

				li_indiv_by_age_sampled=self.resize_sample_to_meet_size_criteria( 
															li_indiv_by_age_collected )	


				#We rely on the genpopfilemanager object to sort 
				#these indices when we pass them to the def,
				#subsampleIndividualsByNumberList (see below).
				dli_indiv_index_lists_by_pop_number[ i_pop_number ] = \
													li_indiv_by_age_sampled
			#end for each pop number

			#for sample param value we use "c" to indicate "cohorts"
			if self.sampleparams.sample_tag is not None:
				s_this_subsample_name = self.sampleparams.sample_tag
			else:
				s_this_subsample_name=make_subsample_tag( \
												self.sampleparams.sample_param_value, 
												i_replicate_number, 
												SCHEME_COHORTS )
			#end if tag is not None
			


			self.filemanager.subsampleIndividualsByNumberList( \
									dli_indiv_index_lists_by_pop_number,
									s_this_subsample_name )

		#end for each replicate
		return
	#end doSample
#end class GenepopFileSamplerIndividualsAgeStructureCohorts

class GenepopFileSamplerIndividualsAgeStructureCohortsPercentage( \
					GenepopFileSamplerIndividualsAgeStructureCohorts ):
	'''
	Sublcass of GenepopFileSamplerIndividualsAgeStructureCohorts.  The only revision
	fo the parent class is in def resize_sample_to_meet_size_criteria.  For this
	subclass we use the proportion attribute to subsample, whereas in the parent
	class we apply max indiv per pop.
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSamplerIndividualsAgeStructureCohorts.__init__( \
											self, o_genepopfilemanager, 
												o_genepopfilesampleparams )
		return
	#end __init__

	def resize_sample_to_meet_size_criteria( self, li_indiv_by_age_collected ):
		'''
		This def overrides its counter part in the parent class.  Given the 
		individuals collected by age, check min/max limits and subsample the 
		requested proportion (via sample params object attribute "proportion"). 
		(Alternatively, In the parent class,  it is the max_total_loci
		that limits the sample size.)
		'''

		i_tot_collected=len( li_indiv_by_age_collected )

		li_indiv_by_age_sampled=None

		if i_tot_collected < self.sampleparams.min_indiv_per_gen:
			s_msg="In GenepopFileSamplerIndividualsAgeStructureCohortsPercentage " \
					+ "instance, def resize_sample_to_meet_size_criteria " \
					+ "after sampling cohorts, total collected, " \
					+ str( i_tot_collected ) \
					+ ", is less than the value given for " \
					+ "the minimum pop size, " \
					+ str( self.sampleparams.min_indiv_per_gen ) \
					+ "."
			raise Exception ( s_msg )
		if i_tot_collected > self.sampleparams.max_indiv_per_gen:
			s_msg="In GenepopFileSamplerIndividualsAgeStructureCohorts " \
					+ "instance, def resize_sample_to_meet_size_criteria " \
					+ "after sampling cohorts, total collected, " \
					+ str( i_tot_collected ) \
					+ ", is greader than the value given for " \
					+ "the maximum pop size, " \
					+ str( self.sampleparams.max_indiv_per_gen ) \
					+ ".  For percentage sampling, unlike "  \
					+ "Cohort sampling without a percentage, " \
					+ "in which the max number is sampled randomly, " \
					+ "in the percentage scheme, cohort samples over " \
					+ "the max are treated as invalid."
			raise Exception( s_msg )
		else:
			i_sample_size=None
			try:
				'''
				In honor of python version uncertanties, we
				cast all operands and results.  For example, 
				inpython2, round returns a float.  In python3,
				at least for round with a single arg, an int is 
				returned.
				'''
				i_sample_size=int( \
						round( float( i_tot_collected )*self.sampleparams.proportion ) )

				li_indiv_by_age_sampled=random.sample( \
									li_indiv_by_age_collected,
												i_sample_size )
										
			except Exception as oex:
				s_sample_error_msg= \
					"In GenepopFileSamplerIndividualsAgeStructureCohortsPercentage" \
						+ "instance, def resize_sample_to_meet_size_criteria, "  \
						+ "random.sample failed on list of " \
						+ str( len( li_indiv_by_age_collected ) ) \
						+ " individuals.  Target proportioin to be sampled: " \
						+ str( i_sample_size  ) + "."
				s_msg=s_sample_error_msg \
						+ "  Exception message: " + str( oex ) + "."
				raise Exception( s_msg )
			#end try . . . except
		#end if too few, error, else if too many, error, else sample proportion.

		return li_indiv_by_age_sampled
	#end resize_sample_to_meet_size_criteria 

#end class GenepopFileSamplerIndividualsAgeStructureCohortsPercentage

class GenepopFileSampleParamsAgeStructureRelateds( GenepopFileSampleParams ):

	def __init__( self, o_genepop_indiv_id_fields, 
								li_population_numbers,
								f_percent_relateds_per_gen,
								i_min_individuals_per_gen,
								i_max_individuals_per_gen,
								s_population_subsample_name="population_numbers",
								i_replicates=1,
								s_sample_param_value="r",
								s_sample_tag=None ):

			GenepopFileSampleParams.__init__(self, 
					li_population_numbers=li_population_numbers, 
					s_population_subsample_name=s_population_subsample_name,
					s_sample_tag=s_sample_tag )

			self.__fields=o_genepop_indiv_id_fields	
			self.__percent_relateds=f_percent_relateds_per_gen
			self.__max_individuals_per_gen=i_max_individuals_per_gen
			self.__min_individuals_per_gen=i_min_individuals_per_gen
			self.__replicates=i_replicates
			self.__sample_param_value=s_sample_param_value

			#the param value field used to construct the
			#subsample name in the sampler member genpopfilemanager
			#object (see def make_subsample_tag).
			self.__sample_param_value=s_sample_param_value
			return
	#end __init__

	@property
	def fields( self ):
		return self.__fields
	#end fields

	@property
	def max_indiv_per_gen( self ):
		return self.__max_individuals_per_gen
	#end indiv_per_gen

	@property
	def min_indiv_per_gen( self ):
		return self.__min_individuals_per_gen
	#end indiv_per_gen
	
	@property
	def percent_relateds( self ):
		return self.__percent_relateds
	#end percent_relateds

	@property
	def replicates( self ):
		return self.__replicates
	#end replicates

	@property
	def sample_param_value( self ):
		return self.__sample_param_value
	#end sample_param_value

#end class GenepopFileSampleParamsAgeStructureRelateds

class GenepopFileSamplerIndividualsAgeStructureRelateds( GenepopFileSampler ):
	'''
	This sampler class meant to implement Tiago's sampling code in his
	sampleIndivsRelated.py module.  It samples pairs of individuals who
	share parentage.  The GenepopFileSampleParams object used by instances
	of this class has the values Tiagos module takes at the command line 
	that restrict the fraction of indiv (per gen) who should be siblings,
	as well as a total individuals per generation.  Note that his
	startGen endGen paramters are already implemented via the Sampler's
	li_population_numbers parameter.
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, 
											o_genepopfilesampleparams )
		return
	#end __init__

	def __get_siblings( self, dli_indiv_index_by_parentage, 
										i_target_total_relateds ):
		'''
		Follows very closely Tiago's def sampleIndivsRelated.getSibs.
		'''
		li_siblings_collected=[]
		lt_done_parents=[]	

		i_total_relateds_not_yet_collected=i_target_total_relateds
		
		while i_total_relateds_not_yet_collected > 0:
			b_have_more=False

			for ts_parents, li_siblings in dli_indiv_index_by_parentage.items():

				if ts_parents in lt_done_parents:
					continue
				#end if parents in done-parents
				
				lt_done_parents.append( ts_parents )

				if len( li_siblings ) > 1:

					b_have_more=True
					li_siblings_collected.append( li_siblings[ 0 ] )
					li_siblings_collected.append( li_siblings[ 1 ] )

					i_total_relateds_not_yet_collected -= 2

					break
				#end if number sibs > 1

			#end for each parent/siblings item

			if b_have_more == False:
				s_msg="In GenepopFileSamplerIndividualsAgeStructureRelateds " \
						+ "instance, def __get_siblings, " \
						+ "not enough relateds. " \
						+ "Target total: " + str( i_target_total_relateds ) \
						+ ".  Total not collected: " \
						+ str( i_total_relateds_not_yet_collected ) \
						+ "."
				raise Exception( s_msg )
			#end if too few relateds
		#end while target total > 0
		return li_siblings_collected
	#end __get_siblings

	def doSample( self ):
		'''
		Sample siblings in pairs/parentage until the percent sibs threshold
		is reached, then pad with non-relateds.  See Tiagos code in his 
		sampleIndivsRelated.py module.
		'''
		FIELD_NAME_AGE="age"
		FIELD_NAME_MOTHER="mother"
		FIELD_NAME_FATHER="father"

		#estimator driver needs a pop number subsample when it adds calls to the NeEstimator:
		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers,
													s_subsample_tag=self.sampleparams.population_subsample_name )

		dli_indiv_index_lists_by_pop_number={}
		
		i_replicate_count=self.sampleparams.replicates

		for i_replicate_number in range(i_replicate_count ):

			for i_pop_number in self.sampleparams.population_numbers:

				ls_id_list=self.filemanager.getListIndividuals( i_pop_number )
				'''
				We assume that the list of Id's in the individual list
				is indexed such that the zeroth id corresponds to the first
				indiv as ordered in the genepop file, the [1] indexed id
				is the second indiv, etc.
				'''
				i_tot_indiv=len( ls_id_list )

				dli_indiv_index_by_parentage={}
				li_all_indivs_this_pop=[]

				'''
				Note that in py3, you can divide 2 ints, at least
				when one's a literal like "100", and get a float
				but in py2 you get the floor of the ratio, i.e. zero
				for any ratio < 1/1.  Note that Tiago's sampleIndivsRelated.py
				code has the  "int( arg[2] )/100" formulation, so that
				the code is no longer py2 compatible without his import statement:
				from __future__ import division.

				We try version-neutral syntax:
				'''

				f_fraction_relateds=self.sampleparams.percent_relateds / 100.0

				assert type( f_fraction_relateds ) == float,  \
						"In GenepopFileSamplerIndividualsAgeStructureRelateds Instance, " \
								+ "def doSample, non-float result of division."

				for idx in range( i_tot_indiv ):

					s_id=ls_id_list[ idx ]
					o_id_vals=GenepopIndivIdVals( s_id, 
										self.sampleparams.fields )
					i_age=o_id_vals.getVal( FIELD_NAME_AGE )

					if i_age > 1:
						continue
					#end if too old, continue

					i_mother=o_id_vals.getVal( FIELD_NAME_MOTHER )
					i_father=o_id_vals.getVal( FIELD_NAME_FATHER )

					ti_parentage=( i_mother, i_father )

					'''
					Note that idx+1 gives the number of the individual as ordered by its
					entry in the "pop" section of this pop in the genepop file, as used
					by the genepopfilemanager object to point to it's byte address in 
					the file.  Thus it's our way of collecting samples of individuals 
					and passing them into the genepop file manager object's subsampling 
					records (its attribute __indiv_subsamples).
					'''
					i_indiv_number=idx+1
					li_all_indivs_this_pop.append( i_indiv_number )
					dli_indiv_index_by_parentage.setdefault( \
								ti_parentage, [] ).append( i_indiv_number ) 

				#end for each individual's id	
				
				i_tot_indivs=len( li_all_indivs_this_pop )

				i_target_total_indivs=i_tot_indivs

				#If too few indivs, error, else reduce the target total if over
				#the max, to the max
				if i_target_total_indivs < self.sampleparams.min_indiv_per_gen:
					s_msg="In GenepopFileSamplerIndividualsAgeStructureRelateds, " \
							+ "instance, total individuals, " \
							+ str( i_tot_indivs ) \
							+ "is under the value given as minimum, " \
							+ str( self.sampleparams.min_indiv_per_gen ) \
							+ "."
					raise Exception( s_msg )
				elif i_target_total_indivs > self.sampleparams.max_indiv_per_gen:
					i_target_total_indivs=self.sampleparams.max_indiv_per_gen
				#end if total individuals under min, error


				i_target_total_relateds=i_target_total_indivs * f_fraction_relateds
				li_relateds_collected=self.__get_siblings( dli_indiv_index_by_parentage, 
																	i_target_total_relateds )
			
				for i_related in li_relateds_collected:
					li_all_indivs_this_pop.remove( i_related )
				#end for each related collected

				#rename for clarity
				li_individuals_with_relateds_removed=\
									li_all_indivs_this_pop

				i_total_relateds_collected=len( li_relateds_collected )

				i_total_indiv_with_relateds_removed=len( li_individuals_with_relateds_removed )

				i_non_relateds_needed_to_make_total= i_target_total_indivs \
													- i_total_relateds_collected
				li_non_relateds_collected = []

				if i_non_relateds_needed_to_make_total > 0:

					try:
						li_non_relateds_collected=random.sample( \
											li_individuals_with_relateds_removed, 
												i_non_relateds_needed_to_make_total )
					except Exception as oex:

						#We may be changing the algorithm to test
						#for the sample size vs the length of the list sampled
						#but for now we catch errors:
						s_sample_error_msg= \
								"In GenepopFileSamplerIndividualsAgeStructureRelateds " \
								+ "instance, def doSample, "  \
								+ "random.sample failed on list of " \
								+ str( len( li_individuals_with_relateds_removed ) ) \
								+ " individuals.  Target total to be sampled: " \
								+ str( i_non_relateds_needed_to_make_total ) + "."

						s_msg=s_sample_error_msg + "  Exception: " + str( oex ) + "."
						raise Exception( s_msg )
					#try . . . except . . . 

				elif i_non_relateds_needed_to_make_total < 0:
					'''
					Not sure this case is possible, but suspect it may be
					due either to rounding, or the pairwise collecting of
					siblings.  We may after trials, decide to except an overage
					of one, but for now let's throw an error:
					'''

					s_msg="In GenepopFileSamplerIndividualsAgeStructureRelateds " \
								+ "instance, def doSample, "  \
								+ "relateds collected, " \
								+ str( i_total_relateds_collected ) \
								+ ", exceeds the maximum set as valid, " \
								+ str( self.sampleparams.max_indiv_per_gen ) \
								+ "."
					raise Exception
				#end if need to collect at least one non_relateds

				li_indiv_sample=li_relateds_collected + li_non_relateds_collected

				dli_indiv_index_lists_by_pop_number[ i_pop_number ] = li_indiv_sample
			#end for each pop number

			s_this_subsample_name=None

			if self.sampleparams.sample_tag is not None:
				s_this_subsample_name=self.sampleparams.sample_tag
			else:
				#for sample param value we use "r" to indicate "relateds"
				s_this_subsample_name=make_subsample_tag( \
												self.sampleparams.sample_param_value, 
												i_replicate_number, 
												SCHEME_RELATEDS )
			#end if we have a tag param, else make it

			self.filemanager.subsampleIndividualsByNumberList( \
									dli_indiv_index_lists_by_pop_number, 
													s_this_subsample_name )
		#end for each replicate
		return
	#end doSample
#end class GenepopFileSamplerIndividualsAgeStructureRelateds

class GenepopFileSamplerLociByRangeAndTotal( GenepopFileSampler ):
	'''
	Sample loci from the ith to the jth, as listed in the 
	genepop file individual entries, and, if the max_total_loci 
	is given, trunctate the total loci to this number by random sampling.
	'''

	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, o_genepopfilesampleparams )
		return
	#end __init__

	def doSample( self ):

		for i_replicate_number in range( self.sampleparams.replicates ):

			s_loci_subsample_tag=None
			if self.sampleparams.sample_tag is not None:
				s_loci_subsample_tag=self.sampleparams.sample_tag
			else:
				s_loci_subsample_tag=make_subsample_tag( self.sampleparams.sample_param_value,
															i_replicate_number,
															SCHEME_LOCI )
			#end if tag param exits use it, else make one

			self.filemanager.subsampleLociByRangeAndMax( self.sampleparams.min_loci_position,
															self.sampleparams.max_loci_position,
															s_loci_subsample_tag,
															self.sampleparams.max_total_loci )
		#end for each replicate

		return
	#end doSample
#end class GenepopFileSamplerLociByRangeAndTotal

class GenepopFileSamplerLociByRangeAndPercentage( GenepopFileSampler ):
	'''
	Sample loci from the ith to the jth, as listed in the 
	genepop file individual entries.  Then, randomly select a subsample
	by proportion, as given by the sample params "proportion" argument.
	'''

	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, o_genepopfilesampleparams )
		return
	#end __init__

	def doSample( self ):

		for i_replicate_number in range( self.sampleparams.replicates ):

			s_loci_subsample_tag=None
			if self.sampleparams.sample_tag is not None:
				s_loci_subsample_tag=self.sampleparams.sample_tag
			else:
				s_loci_subsample_tag=make_subsample_tag( self.sampleparams.sample_param_value,
															i_replicate_number,
															SCHEME_LOCI )
			#end if tag param exits use it, else make one

			self.filemanager.subsampleLociByRangeAndProportion( self.sampleparams.min_loci_position,
																self.sampleparams.max_loci_position,
																s_loci_subsample_tag,
																self.sampleparams.proportion )
		#end for each replicate

		return
	#end doSample
#end class GenepopFileSamplerLociByRangeAndTotal



class GenepopFileSamplerNone( GenepopFileSampler ):
	'''
	Does no sampling, except to apply a min and max pop size.  If
	the population size exceeds the max, the max number is randomly
	selected from among the individuals.
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, o_genepopfilesampleparams )
		return
	#end __init__

	def doSample( self ):
		'''
		Simply add a subsample set that mimics the original
		genepop pos, unless the pop indiv count is under min,
		in which case reduce the sample to zero, or the orignal
		exceeds the max, in which case randomly select the max
		number of individuals.
		'''
		
		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers,
													s_subsample_tag=self.sampleparams.population_subsample_name )
		'''
		Despite the fact that replicates will be indentical, we
		still perform multi replicates if the replicates>1,
		to keep form with other sampler schemes.
		'''
		for i_replicate_number in range( self.sampleparams.replicates ): 

			s_this_subsample_name=None

			if self.sampleparams.sample_tag is not None:
				s_this_subsample_name=self.sampleparams.sample_tag
			else:
				s_this_subsample_name=make_subsample_tag( \
												self.sampleparams.sample_param_value, 
											i_replicate_number, 
											SCHEME_NONE )
			#end if sample tag exits use, else make one

			self.filemanager.subsampleIndividualsByPopSize( self.sampleparams.min_pop_size,
															self.sampleparams.max_pop_size,
															s_this_subsample_name )
		#end for each replicate

		return
	#end def doSample
#end class GenepopFileSamplerNone

class GenepopFileSamplerIndividualsByProportion( GenepopFileSampler ):
	'''
	GenepopFileManager object that samples the individuals in each population
	according one or more proportions (percentages).
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, o_genepopfilesampleparams )
		return
	#end __init __
	
	def doSample( self ):
		'''
		as of Mon Jul 11 20:17:02 MDT 2016, for simplicity, the GenepopFileManager subsampling
		defs that subsample individuals or loci, do so across all populations,
		so that the subset of populations given by this objects member sampleparams property 
		"population_numbers", will only be applied as a filter when writeGenePopFile (or printGenePopFile)
		is applied to this objects GenepopFileManager object (self.filemanager ). The call
		to the GenepopFileManager.writeGenePopFile, will need to include among its args the 
		population subsample name ( assigned as the GenepopFileSampleParams object's
		member "population_subsample_name") 
		'''

		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers, 
				s_subsample_tag=self.sampleparams.population_subsample_name )

		lf_proportions=self.sampleparams.proportions
		i_total_replicates=self.sampleparams.replicates

		for f_proportion in lf_proportions:
			for i_replicate_number in range( i_total_replicates ):

				s_subsampletag=None

				if self.sampleparams.sample_tag is not None:
					s_subsampletag=self.sampleparams.sample_tag
				else:
					#standardized subsample tag uses the proportion and the rep number:
					#note that the "." char delimiter will need to be replaced by a diff
					#char when using this tag to name input or output file names for
					#NeEstimator (which truncates filenames using pattern .* for some of 
					#its output files)
					s_subsampletag=make_subsample_tag(  f_proportion, i_replicate_number , SCHEME_PROPORTION )
				#end if tag exists use it else make one

				self.filemanager.subsampleIndividualsRandomlyByProportion( f_proportion, s_subsampletag ) 
			#end for each replicate number	
		#end for each proportion
		return
#end class GenepopFileSamplerIndividualsByProportion

class GenepopFileSamplerIndividualsByRemoval( GenepopFileSampler ):
	'''
	GenepopFileSampler object that samples individuals in each population
	according to an N-removal scheme, that is, by removing N individuals 
	randomly from the population, some M number of times, for some list of Ns
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, o_genepopfilemanager, 
											o_genepopfilesampleparams )
		return
	#end __init__

	def __do_remove_one( self ):

		'''
		if the member GenepopFileSampleParamsRemoval flag
		"b_do_all_combos_when_n_equals_one" is True,
		then this def gets called, which for each pop
		in the pop list, with M indiv, is subsampled
		M times, by turns leaving out the nth indiv for N
		in 1,2,3...M
		'''

		li_pop_numbers=self.sampleparams.population_numbers

		for i_pop_number in li_pop_numbers:
			i_tot_indiv=self.filemanager.getIndivCountForPop( i_pop_number ) 

			for i_indiv in range( 1, i_tot_indiv + 1 ):

				s_indiv_subsample_tag=make_subsample_tag( 1, i_indiv, SCHEME_REMOVAL )

				self.filemanager.subsampleIndividualsLeaveNthOutFromPop( i_indiv, 
																		i_pop_number,
																		s_indiv_subsample_tag )
			#end for each indiv, leave it out of sample
		#end for each pop number
		return
	#end __do_remove_one

	def doSample( self ):
		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers, 
				s_subsample_tag=self.sampleparams.population_subsample_name )
		
		li_n_values=self.sampleparams.n_to_remove
		i_replicate_total=self.sampleparams.replicates

		for i_n in li_n_values:
			if i_n == 1 \
					and self.sampleparams.do_all_combos_when_n_equals_one == True:
				self.__do_remove_one()
			else:
				for idx in range( i_replicate_total ):

					s_subsample_tag=None
					if self.sampleparams.sample_tag is not None:
						s_subsample_tag=self.sampleparams.sample_tag
					else:
						s_subsample_tag=make_subsample_tag( str( i_n ),  idx, SCHEME_REMOVAL )
					#end if we have a tag param else make one

					self.filemanager.subsampleIndividualsMinusRandomNFromEachPop( i_n, s_subsample_tag )
				#end for each replicate
			#end if n==1, else not
		#end for each n value

		return
	#end doSample
#end class GenepopFileSamplerByRemoval

class GenepopFileSamplerIndividualsByCriteria( GenepopFileSampler ):
	'''
	Samples by criteria applied to fields in individual ids.  
	Instances of this class use the sample params class GenepopFileSampleParamsCriteria
	To pass along to their GenepopFileManager instance attributes the criteria
	for selecting individuals.
	'''

	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, 
						o_genepopfilemanager, 
						o_genepopfilesampleparams )
		return
	#end __init__

	def doSample( self ):

		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers, 
				s_subsample_tag=self.sampleparams.population_subsample_name )

		i_replicate_total=self.sampleparams.replicates
		i_num_criteria=self.sampleparams.criteria.criteriacount

		for idx in range( i_replicate_total ):

			s_subsample_tag = None	

			if self.sampleparams.sample_tag is not None:
				s_subsample_tag=self.sampleparams.sample_tag
			else:
				s_subsample_tag=make_subsample_tag( "c"+ str(i_num_criteria), idx, SCHEME_CRITERIA )
			#end if param tag exits, else make one
			
			self.filemanager.subsampleIndividualsByIdCriteria( self.sampleparams.fields,
														self.sampleparams.criteria,
														s_subsample_tag,
														i_min_pop_sample_size=self.sampleparams.min_sampled_pop_size,
														i_max_pop_sample_size=self.sampleparams.max_sampled_pop_size )
		#end for indexes in range of replicate total
		return
	#end doSample

#end class GenepopFileSamplerIndividualsByCriteria

class GenepopFileSamplerIndividualsByCriteriaFactored( GenepopFileSampler ):
	'''
	Motivation for class creation:  need a way to sample cohorts (indiv
	of a pop with same age-value) for multiple ages for each pop in 
	a genepop file, and then, for each cohort for a give pop, apply a maximum
	pop size (i.e. a max cohort size).

	To that end added to class GenepopFileSampleParamsCriteria a "__max_pop_size"
	attribute, used by this class, which can sample as above by client providing
	a GenepopFileSampleParamsCriteria object with one criteria for each cohort
	(i.e. %age%==i, to get cohort for individuals with age i).  

	To get s factored set such as the cohort descripted above, this class
	is similar to GenepopFileSamplerIndividualsByCriteria, but
	instead of selecting individuals that meet all the criteria (as provided
	by the GenepopIndivCriterion instances wrapped in the GenepopIndivCriteria
	object member of the GenepopFileSampleParamsCriteria object), each criterion
	is first sampled and added to the GenepopFileManager attribute as a separate
	subsample.  After all subsamples are created, then, for each population in
	the population list (as given by the GenepopFileSampleParamsCriteria object)
	they are combined (set.union) by the def in the GenepopFileManager 
	combineIndividualSubsamples.
	'''

	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, 
						o_genepopfilemanager, 
						o_genepopfilesampleparams )
		return
	#end __init__

	def doSample( self ):

		self.filemanager.subsamplePopulationsByList( self.sampleparams.population_numbers, 
				s_subsample_tag=self.sampleparams.population_subsample_name )

		i_replicate_total=self.sampleparams.replicates
		
		i_num_criteria=self.sampleparams.criteria.criteriacount

		ls_temp_names_subsamples=[]

		for idx in range( i_replicate_total ):

			s_subsample_tag=None

			if self.sampleparams.sample_tab is not None:
				s_subsample_tag=self.sampleparams.sample_tag
			else:
				s_subsample_tag=make_subsample_tag( "c"+ str(i_num_criteria), idx, SCHEME_CRITERIA )
			#end if tag param exists else make one

			for idx in self.sampleparams.criteria.critera_count:

				s_temp_subsample_name=s_subsample_tag + "temp_" + str( idx )
				ls_temp_names_subsamples.append( s_temp_subsample )

				#make a new criteria object for the file manager,
				#consisting of only the current criterion:
				o_criteria_consisiting_of_this_criterion= \
						self.sampleparams.criteria.getSubsetOfCriteriaAsNewCriteriaObject( [ idx ] )
			
				self.filemanager.subsampleIndividualsByIdCriteria( self.sampleparams.fields,
															o_criteria_consisiting_of_this_criterion,
															s_temp_subsample_name,
															i_max_pop_sample_size=self.sampleparams.max_sampled_pop_size )
		
				self.filemanager.combineIndividualSubsamples( ls_temp_names_subsamples, 
												s_tag_for_combined_subsample=s_subsample_tag )	

				self.filemanager.removeIndividualSubsamples( ls_temp_names_subsamples )

			#end for indexes in range of replicate total
		return
	#end doSample
#end class GenepopFileSamplerIndividualsByCriteriaFactored


class GenepopFileSamplerIndividualsByCriteriaGrouped( object ):
	'''
	Motivaing case:  Need a way to implement Tiago's sibling sampling
	scheme.  As such, I need to group individuals in sim-generated
	pops, from the AgeStructureNe code, by parentage (sibling groups,
	defined, for two individuals,  as indiv_1.mother==indiv_2.mother, 
	and same for father), operating only on individuals of age==1.  

	I'm generalizing the case to be able to group indiviudals (in a given
	pop inside a genepop file) by matching their field values, for one or
	more fields.  Further, this sampling would then be followed by applying
	a criteria to each individual.
	'''
	def __init__( self, o_genepopfilemanager, o_genepopfilesampleparams ):
		GenepopFileSampler.__init__( self, 
						o_genepopfilemanager, 
						o_genepopfilesampleparams )
		return
	#end __init__

	def doSample( self ):
		ltv_uniq_value_combos = \
			self.filemanager.getListTuplesValuesIndivIdFields( self.sampleparams.fields, 
													self.sampleparams.grouped_fields )
		ls_temp_subsample_names=[]

		i_combo_count=0
		for tv_value_combo in ltv_uniq_value_combos:
			i_combo_count += 1
			ls_operands=[]
			for idx in range( len( tv_value_combo ) ):
				v_value=tv_value_combo[ idx ]
				s_field_name=self.sampleparams.grouped_fields[ idx ]
				s_field_as_variable=gic.make_test_variable( s_field_name )
				s_test_operand=s_field_as_variable + "==" + str( v_value )
				ls_operands.append( s_test_operand )
			#end for each value, make operand in test expression

			s_test_expression=" and ".join(  ls_operands )

			o_criteria_for_these_grouped_values=self.sampleparams.criteria.copy()

			#Note: first arg is the criterion name, not important
			#for our current algorithm:
			o_criteria_for_these_grouped_values.addCriterion( \
													"group", 
													self.sampleparams.grouped_fields,
													s_test_expression )
			s_subsample_name=None
			if self.sampleparams.sample_tag is not None:
				s_subsample_name=self.sampleparams.sample_tag
			else:
				s_subsample_name="combo_" + str( i_combo_count )
			#end if we have a tag param else make one

			ls_temp_subsample_names.append( s_subsample_name )

			self.filemanager.subsampleIndividualsByIdCriteria( self.sampleparams.fields, 
																o_criteria_for_these_grouped_values,
																s_subsample_name,	
																self.sampleparams.max_sampled_pop_size )
		#end for each tuple of indiv id field values

		return
	#end doSample

#end class GenepopFileSamplerIndividualsByCriteriaGrouped

if __name__ == "__main__":

	import sys
	import MyUtilities.misc_utilities as modut
	import genepopfilemanager as gpf	
	import test_code.testdefs as td

	ls_args=[ "genepop file", "test number" ]

	s_usage=modut.do_usage_check( sys.argv, ls_args )

	if s_usage:
		print( s_usage )
		sys.exit()
	#end if usage
	
	s_genepopfile=sys.argv[ 1 ]
	s_test_number=sys.argv[ 2 ]

	ddefs={ 1:td.testdef_genepopfilesample_1 , 2: td.testdef_genepopfilesample_2 }
	
	ddefs[ int( s_test_number ) ] ( s_genepopfile )

#end if main

