slickint
========

A way to deal with tables with more than 22 columns using Scala's slick ORM

Scala case classes and tuples have a hard limit of 22 elements, which makes using Slick for tables > 22 elements hard. SlickInt allows you to get around this problem a little easier.

## Step 1: Obtain the slickint.py class in this repo

## Step 2: Write out your interface class (example below)
```
package com.hulu.jobscheduler.logmanager
import scala.slick.driver.MySQLDriver.simple._
import java.sql.Date
table=Job, primaryKey=jobId, dbname=job, *=jobId ~ name ~ dependsOn ~ jobType ~ runPriority ~ isKPI
jobId               : Int           : jobid
name                : String        : name
enabled             : Int           : enabled
minDateRangeStart   : Long          : mindaterangestart
fileBatch           : Int           : filebatch
dependsOn           : Int?          : dependson
allowPickup         : Int           : allowpickup
jobType             : Int?          : jobtype
minDate             : Date?         : mindate
maxDate             : Date?         : maxdate
hoursBeforeDay      : Int?          : hoursbeforeday
hoursAfterDay       : Int?          : hoursafterday
hardStopAction      : Int           : hardstop_action
inputFileType       : String        : inputfiletype
ignoreTrailingData  : Int           : ignoretrailingdata
ignoreLeadingData   : Int           : ignoreleadingdata
priority            : Int?          : priority
errorThreshold      : Int?          : error_threshold
runPriority         : Int           : runpriority
regionId            : Int           : regionid
harpyOutputBasePath : String?       : harpy_output_basepath
customJar           : String?       : custom_jar
isKPI               : Int           : isKPI
```

There are three types of lines:
* A line with two colons - this represents a column in the database table. The first element is the name of the column in the ORM object, the second is the type (Nullable types are denoted by "?"), the third is the name of the column in the database
* A table header line, this starts with "table" and must have the (table, primaryKey, dbname, *) attributes defined
* Any other line, which is reproduced as it appears (useful for declaring package and import information)

## Step 3: Generate the Slick object with the following command:
```
python slickint.py [input-filename].slickint > [output-filename].scala
```

For the above interface definition, the following class will be generated:

```scala
package com.hulu.jobscheduler.logmanager
import scala.slick.driver.MySQLDriver.simple._
import java.sql.Date
object Job extends Table[(Int, String, Option[Int], Option[Int], Int, Int)]("job") {
  def part1 = allowPickup ~ maxDate ~ regionId ~ ignoreTrailingData ~ jobId ~ jobType ~ fileBatch ~ ignoreLeadingData ~ minDateRangeStart ~ inputFileType ~ customJar ~ priority ~ runPriority ~ isKPI ~ hoursBeforeDay ~ errorThreshold ~ hoursAfterDay ~ minDate ~ hardStopAction ~ name <>(JobData1, JobData1.unapply _)
  def part2 = harpyOutputBasePath ~ enabled ~ dependsOn <>(JobData2, JobData2.unapply _)
  def all = (part1, part2)
  def * = jobId ~ name ~ dependsOn ~ jobType ~ runPriority ~ isKPI
  def allowPickup = column[Int]("allowpickup")
  def maxDate = column[Option[Date]]("maxdate")
  def regionId = column[Int]("regionid")
  def ignoreTrailingData = column[Int]("ignoretrailingdata")
  def jobId = column[Int]("jobid")
  def jobType = column[Option[Int]]("jobtype")
  def fileBatch = column[Int]("filebatch")
  def ignoreLeadingData = column[Int]("ignoreleadingdata")
  def minDateRangeStart = column[Long]("mindaterangestart")
  def inputFileType = column[String]("inputfiletype")
  def customJar = column[Option[String]]("custom_jar")
  def priority = column[Option[Int]]("priority")
  def runPriority = column[Int]("runpriority")
  def isKPI = column[Int]("isKPI")
  def hoursBeforeDay = column[Option[Int]]("hoursbeforeday")
  def errorThreshold = column[Option[Int]]("error_threshold")
  def hoursAfterDay = column[Option[Int]]("hoursafterday")
  def minDate = column[Option[Date]]("mindate")
  def hardStopAction = column[Int]("hardstop_action")
  def name = column[String]("name")
  def harpyOutputBasePath = column[Option[String]]("harpy_output_basepath")
  def enabled = column[Int]("enabled")
  def dependsOn = column[Option[Int]]("dependson")
}
case class JobData1(allowPickup: Int, maxDate: Option[Date], regionId: Int, ignoreTrailingData: Int, jobId: Int, jobType: Option[Int], fileBatch: Int, ignoreLeadingData: Int, minDateRangeStart: Long, inputFileType: String, customJar: Option[String], priority: Option[Int], runPriority: Int, isKPI: Int, hoursBeforeDay: Option[Int], errorThreshold: Option[Int], hoursAfterDay: Option[Int], minDate: Option[Date], hardStopAction: Int, name: String)
case class JobData2(harpyOutputBasePath: Option[String], enabled: Int, dependsOn: Option[Int])
case class JobData(data1: JobData1, data2: JobData2) {
  def allowPickup = data1.allowPickup
  def maxDate = data1.maxDate
  def regionId = data1.regionId
  def ignoreTrailingData = data1.ignoreTrailingData
  def jobId = data1.jobId
  def jobType = data1.jobType
  def fileBatch = data1.fileBatch
  def ignoreLeadingData = data1.ignoreLeadingData
  def minDateRangeStart = data1.minDateRangeStart
  def inputFileType = data1.inputFileType
  def customJar = data1.customJar
  def priority = data1.priority
  def runPriority = data1.runPriority
  def isKPI = data1.isKPI
  def hoursBeforeDay = data1.hoursBeforeDay
  def errorThreshold = data1.errorThreshold
  def hoursAfterDay = data1.hoursAfterDay
  def minDate = data1.minDate
  def hardStopAction = data1.hardStopAction
  def name = data1.name
  def harpyOutputBasePath = data2.harpyOutputBasePath
  def enabled = data2.enabled
  def dependsOn = data2.dependsOn
}
object JobConversions {
  implicit def toJobData(someValue: (JobData1, JobData2)) = {
    JobData(someValue._1, someValue._2)
  }
}
```

This can subsequently be accessed like so:
```scala
val jobList = (for (job <- Job) yield job.all).list
      for (jl <- jobList) {
        // The below line relies on the implicit conversion
        val jd: JobData = jl
        print((jd.name, jd.jobId, jd.jobType))
      }
    }
```
