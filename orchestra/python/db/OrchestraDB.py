
__all__ = ["OrchestraDB"]

from Gaugi import Logger, NotSet, StatusCode
from Gaugi.messenger.macros import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from orchestra.db.models import*
from sqlalchemy import and_, or_
import time

from orchestra.constants import *
from orchestra import Cluster

class OrchestraDB(Logger):

  def __init__( self, cluster=Cluster.LPS ):

    Logger.__init__(self)

    if cluster == Cluster.LPS:
      url = DEFAULT_URL_LPS
    elif cluster == Cluster.SDUMONT:
      url = DEFAULT_URL_SDUMONT
    else:
      MSG_FATAL(self, "URL database not defined for this cluster")

    try: # Get the connection and create an session
      MSG_DEBUG( self, "Connect to %s.", url )
      self.__engine = create_engine(url)
      Session= sessionmaker(bind=self.__engine)
      self.__session = Session()
    except Exception as e:
      MSG_FATAL( self, e )


  def getStoragePath(self):

    if self.__cluster is Cluster.LPS:
      return BASEPATH_SG_LPS
    elif self.__cluster is Cluster.SDUMONT:
      return BASEPATH_SG_DUMONT
    else:
      MSG_WARNING( self, "Cluster path not defined.")



  def createTask( self , user, taskName, configFilePath, inputFilePath, outputFilePath, containerImage, cluster,
                  templateExecArgs="{}",
                  secondaryDataPath="{}",
                  etBinIdx=None,
                  etaBinIdx=None,
                  isGPU=False):

    try:
      # Create the task and append into the user area
      task = Task(taskName=taskName,
                  inputFilePath=inputFilePath,
                  outputFilePath=outputFilePath,
                  configFilePath=configFilePath,
                  containerImage=containerImage,
                  # The task always start as registered status
                  status='registered',
                  cluster=cluster,
                  # Extra args
                  templateExecArgs=templateExecArgs,
                  secondaryDataPath=secondaryDataPath,
                  etBinIdx=etBinIdx,
                  etaBinIdx=etaBinIdx,
                  isGPU=isGPU
                  )
      user.addTask(task)
      return task
    except Exception as e:
      MSG_ERROR(self, e)
      return None



  def createJob( self, task, configFilePath, configId, priority=1000, execArgs="{}", isGPU=False ):

    try:
      job = Job( configFilePath=configFilePath,
                 containerImage=task.containerImage,
                 configId=configId,
                 execArgs=execArgs,
                 cluster=task.getCluster(),
                 retry=0,
                 status="registered",
                 priority=priority,
                 isGPU=isGPU
                 )
      task.addJob(job)
      return job
    except Exception as e:
      MSG_ERROR( self, e)
      return None


  def getUser( self, username ):

    if not self.isConnected():
      return None

    try:
      return self.session().query(Worker).filter(Worker.username==username).first()
    except Exception as e:
      MSG_ERROR(self, e)
      return None




  def getTask( self, taskName ):

    if not self.isConnected():
      return None

    try: # Get the task object using the task name as filter
      return self.session().query(Task).filter(Task.taskName==taskName).first()
    except Exception as e:
      MSG_ERROR(self, e)
      return None


  def getAllUsers( self ):
    if not self.isConnected():
      return None

    try:
      return self.session().query(Worker).all()
    except Exception as e:
      MSG_ERROR( self, e)
      return None


  def getAllTasks( self, user ):
    if not self.isConnected():
      return None
    try:
      return user.getAllTasks()
    except Exception as e:
      return None


  def getAllJobs( self, task ):
    if not self.isConnected():
      return None
    try:
      return job.getAllJobs()
    except Exception as e:
      return None




  def isConnected( self ):
    for _ in range(NUMBER_OF_TRIALS):
      try:
        self.session().query(Worker).all()
        return True
      except:
        MSG_WARNING(self, "Data base connection is failed... wainting 5 minutes")
        time.sleep( 5*MINUTE )
        continue
    return False



  def session(self):
    return self.__session


  def commit(self):
    self.session().commit()


  def close(self):
    self.session().close()



  def initialize( self ):
    return StatusCode.SUCCESS



  def execute( self ):
    return StatusCode.SUCCESS


  def finalize( self ):
    self.commit()
    self.close()
    return StatusCode.SUCCESS




  def retryTask( self, taskname ):

    if not self.isConnected():
      return False

    try:
      task = self.getTask( args.taskname  )
    except:
      MSG_ERROR(self, "The task name (%s) does not exist into the data base", taskname)
      return False

    try:
      for job in task.getAllJobs():
        if job.getStatus() == 'failed':
          job.setStatus('assigned')
    except Exception as e:
      MSG_ERROR(self, "Impossible to assigned all failed jobs. error: %s",e)




  def deleteTask( self, taskname ):

    if not self.isConnected():
      return False

    try:
      task = self.getTask( args.taskname  )
    except:
      MSG_ERROR(self, "The task name (%s) does not exist into the data base", taskname)
      return False
    id = task.id
    try:
      self.session().query(Job).filter(Job.taskId==id).delete()
    except Exception as e:
      MSG_ERROR(self, "Impossible to remove Job lines from (%d) task", id)
      return False

    try:
      self.session().query(Task).filter(Task.id==id).delete()
    except Exception as e:
      MSG_ERROR(self, "Impossible to remove Task lines from (%d) task", id)
      return False

    return True




  def getAllMachines(self):
    if not self.isConnected():
      return False

    try:
      return self.session().query(Node).all()
    except Exception as e:
      MSG_ERROR(self, "Impossible to retrieve nodes from database.")
      return []



  def getMachine( self, name ):
    if not self.isConnected():
      return None
    try:
      return self.session().query(Node).filter(Node.name==name).first()
    except Exception as e:
      MSG_ERROR(self, e)
      return None



  def createDataset( self, dataset ):

    if not self.isConnected():
      return None

    try:
      self.session().add(dataset)
      return True
    except Exception as e:
      MSG_ERROR(self, e)
      return False



  def getAllDatasets( self, username):

    if not self.isConnected():
      return None

    try:
      return self.session().query(Dataset).filter(Dataset.username==username).all()
    except Exception as e:
      MSG_ERROR(self, e)
      return None




  def getDataset( self, username, dataset ):

    if not self.isConnected():
      return None

    try:
      return self.session().query(Dataset).filter(and_( Dataset.username==username, Dataset.dataset==dataset) ).first()
    except Exception as e:
      MSG_ERROR(self, e)
      return None





