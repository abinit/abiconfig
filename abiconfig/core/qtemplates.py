"""Template strings used to generate scripts for resource managers."""
from __future__ import unicode_literals, division, print_function, absolute_import

import string

class QueueTemplate(string.Template):
    delimiter = '$$'

    @classmethod
    def from_qtype(cls, qtype):
        for c in QueueTemplate.__subclasses__():
            if c.QTYPE == qtype: return c(c.QTEMPLATE)
        raise ValueError("Cannot find QueueTemplate associated to qtype: %s" % qtype)

    @property
    def supported_qparams(self):
        """
        Dictionary with the supported parameters that can be passed to the
        queue manager (obtained by parsing QTEMPLATE).
        """
        import re
        return re.findall("\$\$\{(\w+)\}", self.QTEMPLATE)

    def substitute(self, subs_dict):
        # might contain unused parameters as leftover $$.
        unclean_template = self.safe_substitute(subs_dict)
        return unclean_template

        # Remove lines with leftover $$.
        clean_template = []
        for line in unclean_template.split('\n'):
            if '$$' not in line:
                clean_template.append(line)

        return '\n'.join(clean_template)


class ShellTemplate(QueueTemplate):
    """Shell template."""
    QTYPE = "shell"

    QTEMPLATE = """\
#!/bin/bash
"""

class SlurmTemplate(QueueTemplate):
    """SLURM template."""
    QTYPE = "slurm"

    QTEMPLATE = """\
#!/bin/bash

#SBATCH --partition=$${partition}
#SBATCH --job-name=$${job_name}
#SBATCH --nodes=$${nodes}
#SBATCH --total_tasks=$${total_tasks}
#SBATCH --ntasks=$${ntasks}
#SBATCH --ntasks-per-node=$${ntasks_per_node}
#SBATCH --cpus-per-task=$${cpus_per_task}
#SBATCH --mem=$${mem}
#SBATCH --mem-per-cpu=$${mem_per_cpu}
#SBATCH --hint=$${hint}
#SBATCH --time=$${time}
#SBATCH	--exclude=$${exclude}
#SBATCH --account=$${account}
#SBATCH --mail-user=$${mail_user}
#SBATCH --mail-type=$${mail_type}
#SBATCH --constraint=$${constraint}
#SBATCH --gres=$${gres}
#SBATCH --requeue=$${requeue}
#SBATCH --nodelist=$${nodelist}
#SBATCH --propagate=$${propagate}
#SBATCH --licenses=$${licenses}
#SBATCH --output=$${_qout_path}
#SBATCH --error=$${_qerr_path}
"""

class PbsProTemplate(QueueTemplate):
    """PbsPro Template"""
    QTYPE = "pbspro"

    QTEMPLATE = """\
#!/bin/bash

#PBS -q $${queue}
#PBS -N $${job_name}
#PBS -A $${account}
#PBS -l select=$${select}
#PBS -l pvmem=$${pvmem}mb
#PBS -l walltime=$${walltime}
#PBS -l model=$${model}
#PBS -l place=$${place}
#PBS -W group_list=$${group_list}
#PBS -M $${mail_user}
#PBS -m $${mail_type}
#PBS -o $${_qout_path}
#PBS -e $${_qerr_path}
"""

class SGETemplate(QueueTemplate):
    """
    Template for Sun Grid Engine (SGE) task submission software.

    See also:

        * https://www.wiki.ed.ac.uk/display/EaStCHEMresearchwiki/How+to+write+a+SGE+job+submission+script
        * http://www.uibk.ac.at/zid/systeme/hpc-systeme/common/tutorials/sge-howto.html
    """
    QTYPE = "sge"

    QTEMPLATE = """\
#!/bin/bash

#$ -account_name $${account_name}
#$ -N $${job_name}
#$ -q $${queue_name}
#$ -pe $${parallel_environment} $${ncpus}
#$ -l h_rt=$${walltime}
# request a per slot memory limit of size bytes.
##$ -l h_vmem=$${mem_per_slot}
##$ -l mf=$${mem_per_slot}
###$ -j no
#$ -M $${mail_user}
#$ -m $${mail_type}
# Submission environment
##$ -S /bin/bash
###$ -cwd                       # Change to current working directory
###$ -V                         # Export environment variables into script
#$ -e $${_qerr_path}
#$ -o $${_qout_path}
"""

class MOABTemplate(QueueTemplate):
    """Template for MOAB. See https://computing.llnl.gov/tutorials/moab/"""
    QTYPE = "moab"

    QTEMPLATE = """\
#!/bin/bash

#MSUB -a $${eligible_date}
#MSUB -A $${account}
#MSUB -c $${checkpoint_interval}
#MSUB -l feature=$${feature}
#MSUB -l gres=$${gres}
#MSUB -l nodes=$${nodes}
#MSUB -l partition=$${partition}
#MSUB -l procs=$${procs}
#MSUB -l ttc=$${ttc}
#MSUB -l walltime=$${walltime}
#MSUB -l $${resources}
#MSUB -p $${priority}
#MSUB -q $${queue}
#MSUB -S $${shell}
#MSUB -N $${job_name}
#MSUB -v $${variable_list}

#MSUB -o $${_qout_path}
#MSUB -e $${_qerr_path}
"""

class BlueGeneTemplate(QueueTemplate):
    """
    Template for LoadLever on BlueGene architectures.

    See:
        http://www.prace-ri.eu/best-practice-guide-blue-gene-q-html/#id-1.5.4.8
        https://www.lrz.de/services/compute/supermuc/loadleveler/
    """
    QTYPE = "bluegene"

    QTEMPLATE = """\
#!/bin/bash
# @ job_name = $${job_name}
# @ class = $${class}
# @ error = $${_qout_path}
# @ output = $${_qerr_path}
# @ wall_clock_limit = $${wall_clock_limit}
# @ notification = $${notification}
# @ notify_user = $${mail_user}
# @ environment = $${environment}
# @ account_no = $${account_no}
# @ job_type = bluegene
# @ bg_connectivity = $${bg_connectivity}
# @ bg_size = $${bg_size}
# @ queue
"""
