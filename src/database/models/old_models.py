import os
import webapp2
import jinja2
from google.appengine.ext import ndb
from google.appengine.api import users
import logging
template_env = jinja2.Environment(
loader=jinja2.FileSystemLoader(os.getcwd()))

from Employee import EmploymentDetails

import datetime

strValidMonths = ["JAN","FEB","MAR","APR","MAR","JUN","JUL","AUG","OCT","SEP","NOV","DEC"]

class Constants(ndb.Expando):
    undefined = None
    _generalError = "General Error"
    strReference = ndb.StringProperty()
    strPolicyNum = ndb.StringProperty()  # Calculated Value BranchCODE/EMPCODE/PolicyNUMBER  ####/#####/#####


    def readReference(self):
        try:
            strtemp = str(self.strReference)

            if not (strtemp == self.undefined):
                return strtemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writeReference(self, strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not (strinput == self.undefined):
                self.strReference = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readPolicyNum(self):
        try:
            strTemp = str(self.strPolicyNum)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writePolicyNum(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strPolicyNum = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def setGeneralError(self,strinput):
        try:
            strinput = str(strinput)
            if strinput == self.undefined:
                self._generalError = strinput
                return True
            else:
                return False
        except:
            return self._generalError

class WorkingPolicy(ndb.Expando):
    strTotalCreated = ndb.IntegerProperty(default=0)
    strActivated = ndb.BooleanProperty(default=False)

    strReference = ndb.StringProperty()
    strPolicyNum = ndb.StringProperty()  # Calculated Value BranchCODE/EMPCODE/PolicyNUMBER  ####/#####/#####


    def readReference(self):
        try:
            strtemp = str(self.strReference)

            if not (strtemp == None):
                return strtemp
            else:
                return None
        except:
            return None

    def writeReference(self, strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not (strinput == None):
                self.strReference = strinput
                return True
            else:
                return False
        except:
            return None

    def readPolicyNum(self):
        try:
            strTemp = str(self.strPolicyNum)
            strTemp = strTemp.strip()

            if not(strTemp == None):
                return strTemp
            else:
                return None
        except:
            return None

    def writePolicyNum(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == None):
                self.strPolicyNum = strinput
                return True
            else:
                return False
        except:
            return None

    def readTotalCreated(self):
        try:
            strTemp = str(self.strTotalCreated)
            strTemp = strTemp.strip()

            if strTemp.isdigit():
                return int(strTemp)
            else:
                return None
        except:
            return None

    def writeTotalCreated(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if strinput.isdigit():
                self.strTotalCreated = strinput
                return True
            else:
                return False
        except:
            return False

    def readActivated(self):
        try:
            return self.strActivated
        except:
            return False

    def writeActivated(self,strinput):
        try:
            if strinput == True:
                self.strActivated = strinput
                return True
            elif strinput == False:
                self.strActivated = strinput
                return True
            else:
                return False
        except:
            return False

    def createNewPolicyNumber(self,strinput):
        try:
            Guser = users.get_current_user()
            logging.info("Create Policy Number Called")
            if Guser:
                logging.info("Maybe Problem is here" + str(strinput))
                strinput = str(strinput)
                logging.info(strinput)
                if strinput.isdigit():
                    self.strTotalCreated = int(strinput) + 1
                    logging.info(msg="Tested True if its Digit")
                else:
                    self.strTotalCreated = 1
                    logging.info(msg="Tested False if its digit")

                self.strActivated = False
                self.strReference = Guser.user_id()
                logging.info(msg="Create Policy Number Called")

                findRequest = EmploymentDetails.query(EmploymentDetails.strReference == Guser.user_id())
                EmployeeList = findRequest.fetch()


                if len(EmployeeList) > 0:
                    Employee = EmployeeList[0]
                else:
                    Employee = EmploymentDetails()

                self.strPolicyNum = str(Employee.strBranchCode) + str(Employee.strEmployeeCode) + str(self.strTotalCreated)

                self.put()
                return self.strPolicyNum
            else:
                logging.info("Tested False if its GUser")
                return None
        except:
            return None

class ResourceAccessRights(Constants):
    """
        If the rights relate to a client who can login into the system then the record will also contain
        the policy number

        if the rights relate to an employee then theres no use for an employment number as all employees can be
        identifiable using only their email hence reference will be enough to identify them
    """
    strEmployeeCode = ndb.StringProperty()

    bolAccessToEmployeesFuneralForm = ndb.BooleanProperty(default=False)
    bolAccessToEmployeesFuneralServiceForm = ndb.BooleanProperty(default=False)
    bolAccessToEmployeesLeadsForm = ndb.BooleanProperty(default=False)
    bolAccessToEmployeesAdminForm = ndb.BooleanProperty(default=False)

    bolAccessToClientsFuneralCoverForm = ndb.BooleanProperty(default=False)
    bolAccessToClientsFuneralServiceForm = ndb.BooleanProperty(default=False)
    bolAccessToClientsFuneralClaimsForm = ndb.BooleanProperty(default=False)
    bolAccessToClientsReferralsForm = ndb.BooleanProperty(default=False)

    bolAccessToStaffChatForm = ndb.BooleanProperty(default=False)
    bolAccessToClientsChatForm = ndb.BooleanProperty(default=False)

    def readEmployeeCode(self):
        try:
            strTemp = str(self.strEmployeeCode)
            return strTemp
        except:
            return ""

    def writeEmployeeCode(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strEmployeeCode = strinput
                return True
            else:
                return False

        except:
            return False

    def setClientsRightsDefault(self):
        try:

            self.bolAccessToClientsFuneralCoverForm = True
            self.bolAccessToClientsFuneralServiceForm = True
            self.bolAccessToClientsFuneralClaimsForm = True
            self.bolAccessToClientsReferralsForm = True
            self.bolAccessToClientsChatForm = True
            return True
        except:
            return False

    def setEmployeeAccessRightsDefault(self):
        try:
            if self.setClientsRightsDefault():
                self.bolAccessToEmployeesFuneralForm = True
                self.bolAccessToClientsFuneralServiceForm = True
                self.bolAccessToEmployeesLeadsForm = True
                return True
            else:
                return False
        except:
            return False

    def setAdminAccessRightsDefault(self):


        try:

            if self.setEmployeeAccessRightsDefault() :
                self.bolAccessToEmployeesAdminForm = True
                return True
            else:
                return False
        except:
            return False

class UserRights(ResourceAccessRights):
    """
        Access to this rights will be given to specific resources by the admin/ managers

        Other rights should be to specific forms where employees users complete tasks

        When Access is given to specific forms sub rights could still be controlled such as the ability to make changes and
        or delete records/policies
        bolCanCreateClientFuneralCover = ndb.BooleanProperty(default=False)
        bolCanDeleteClientPolicy = ndb.BooleanProperty(default=False)
        bolCanEditClientPolicy = ndb.BooleanProperty(default=False)

        bolCanSearchClientPolicies = ndb.BooleanProperty(default=False)
        bolCanPrintConsoleData = ndb.BooleanProperty(default=False)
        bolCanSaveConsoleData = ndb.BooleanProperty(default=False)

        bolCanAssignTasks = ndb.BooleanProperty(default=False)
        bolCanAssignSchedules = ndb.BooleanProperty(default=False)
    """

    bolIsEmployee = ndb.BooleanProperty(default=False)
    bolEmployeesFuneralCoverFormReadAccess = ndb.BooleanProperty(default=False)
    bolEmployeesFuneralCoverFormWriteAccess = ndb.BooleanProperty(default=False)
    bolEmployeesFuneralCoverFormDeleteAccess = ndb.BooleanProperty(default=False)


    bolEmployeesFuneralServicesFormReadAccess = ndb.BooleanProperty(default=False)
    bolEmployeesFuneralServicesFormWriteAccess = ndb.BooleanProperty(default=False)
    bolEmployeesFuneralServicesFormDeleteAccess = ndb.BooleanProperty(default=False)


    bolEmployeesLeadsFormReadAccess = ndb.BooleanProperty(default=False)
    bolEmployeesLeadsFormWriteAccess = ndb.BooleanProperty(default=False)
    bolEmployeesLeadsFormDeleteAccess = ndb.BooleanProperty(default=False)


    bolEmployeesAdminFormReadAccess = ndb.BooleanProperty(default=False)
    bolEmployeesAdminFormWriteAccess = ndb.BooleanProperty(default=False)
    bolEmployeesAdminFormDeleteAccess = ndb.BooleanProperty(default=False)


    bolClientsFuneralCoverFormReadAccess = ndb.BooleanProperty(default=False)
    bolClientsFuneralCoverFormWriteAccess = ndb.BooleanProperty(default=False)
    bolClientsFuneralCoverFormDeleteAccess = ndb.BooleanProperty(default=False)


    bolClientsFuneralServiceFormReadAccess = ndb.BooleanProperty(default=False)
    bolClientsFuneralServiceFormWriteAccess = ndb.BooleanProperty(default=False)
    bolClientsFuneralServiceFormDeleteAccess = ndb.BooleanProperty(default=False)


    bolClientsFuneralClaimsFormReadAccess = ndb.BooleanProperty(default=False)
    bolClientsFuneralClaimsFormWriteAccess = ndb.BooleanProperty(default=False)
    bolClientsFuneralClaimsFormDeleteAccess = ndb.BooleanProperty(default=False)


    bolClientsReferralsFormReadAccess = ndb.BooleanProperty(default=False)
    bolClientsReferralsFormWriteAccess = ndb.BooleanProperty(default=False)
    bolClientsReferralsFormDeleteAccess = ndb.BooleanProperty(default=False)




    def setClientUserRights(self):
        try:
            if self.setClientsRightsDefault():
                self.bolClientsFuneralCoverFormReadAccess = True
                self.bolClientsFuneralCoverFormWriteAccess = True
                self.bolClientsFuneralClaimsFormReadAccess = True
                self.bolClientsFuneralClaimsFormWriteAccess = True
                self.bolClientsFuneralServiceFormReadAccess = True
                self.bolClientsFuneralServiceFormWriteAccess = True
                self.bolClientsReferralsFormReadAccess = True
                self.bolClientsReferralsFormWriteAccess = True
                self.bolIsEmployee = False
                return True
            else:
                return False
        except:
            return False



    def setEmployeeUserRights(self):
        try:
            if self.setClientUserRights() and self.setEmployeeAccessRightsDefault():
                self.bolEmployeesFuneralCoverFormReadAccess = True
                self.bolEmployeesFuneralCoverFormWriteAccess = True
                self.bolEmployeesFuneralServicesFormReadAccess = True
                self.bolEmployeesFuneralServicesFormWriteAccess = True
                self.bolEmployeesLeadsFormReadAccess = True
                self.bolEmployeesLeadsFormWriteAccess = True
                self.bolIsEmployee = True
                return True
            else:
                self.bolIsEmployee = False
                return False
        except:
            self.bolIsEmployee = False
            return False

    def setAdminUserRights(self):
        try:

            if self.setAdminAccessRightsDefault():

                self.bolEmployeesAdminFormReadAccess = True
                self.bolEmployeesAdminFormWriteAccess = True
                self.bolEmployeesAdminFormDeleteAccess = True
            else:
                pass
        except:
            pass

class CompanyDetails(Constants):
    pass

class BranchDetails(Constants):
    """
        When Setting Up Branch Names and Codes must be entered on the Admin Interface of the WebApp
    """
    strCompanyBranchCode = ndb.StringProperty()
    strCompanyBranchName = ndb.StringProperty()
    strCompanyBranchAddress = ndb.StringProperty()
    strCompanyBranchTel = ndb.StringProperty()
    strCompanyBranchEmail = ndb.StringProperty()
    strCompanyBranchManagerName = ndb.StringProperty()
    strCompanyBranchManagerTel = ndb.StringProperty()
    strCompanyBranchManagerEmail = ndb.StringProperty()



    def readCompanyBranchCode(self):
        try:
            strTemp = str(self.strCompanyBranchCode)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writeCompanyBranchCode(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCompanyBranchCode = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readCompanyBranchName(self):
        try:
            strTemp = str(self.strCompanyBranchName)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writeCompanyBranchName(self,strinput):
        try:
            strinput  = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCompanyBranchName = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def writeCompanyBranchAddress(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCompanyBranchAddress = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readCompanyBranchAddress(self):
        try:
            strTemp = str(self.strCompanyBranchAddress)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writeCompanyBranchTel(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCompanyBranchTel = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readCompanyBranchTel(self):
        try:
            strTemp = str(self.strCompanyBranchTel)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writeCompanyBranchEmail(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCompanyBranchEmail = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readCompanyBranchEmail(self):
        try:
            strTemp = str(self.strCompanyBranchEmail)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writeBranchManagerName(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCompanyBranchManagerName = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readBranchManagerName(self):
        try:
            strTemp = str(self.strCompanyBranchManagerName)
            strTemp = strTemp.strip()
            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writeBranchManagerTel(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCompanyBranchManagerTel = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readBrachManagerTel(self):
        try:
            strTemp = str(self.strCompanyBranchManagerTel)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

    def writeBranchManagerEmail(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCompanyBranchManagerEmail = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readBranchManagerEmail(self):
        try:
            strTemp = str(self.strCompanyBranchManagerEmail)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return self.undefined
        except:
            return self._generalError

class PersonalDetails(Constants):

    strTitle = ndb.StringProperty()
    strFullNames = ndb.StringProperty()
    strSurname = ndb.StringProperty()
    strIDNumber = ndb.StringProperty() # Passport Number
    strDateOfBirth = ndb.DateProperty()
    strNationality = ndb.StringProperty()




    def readTitle(self):
        try:
            strtemp = str(self.strTitle)
            strtemp = strtemp.strip()

            if not (strtemp == self.undefined):
                return strtemp
            else:
                return ""

        except:
            return ""

    def writeTitle(self, strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not (strinput == self.undefined):
                self.strTitle = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def writeNames(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strFullNames = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readNames(self):
        try:
            strTemp = str(self.strFullNames)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def readSurname(self):
        try:
            strTemp = str(self.strSurname)
            strTemp = strTemp.strip()

            if not (strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeSurname(self, strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not (strinput == self.undefined):
                self.strSurname = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readIDNumber(self):
        try:
            strTemp = str(self.strIDNumber)
            strTemp = strTemp.strip()

            if not (strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeIDNumber(self, strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not (strinput == self.undefined):
                self.strIDNumber = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readDateOfBirth(self):
        try:
            strtemp = str(self.strDateOfBirth)

            if not (strtemp == self.undefined):
                return strtemp
            else:
                return ""
        except:
            return ""

    def writeDateOfBirth(self, strinput):
        """
             format yyyy-mm-dd
         """
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            Datefields = strinput.split("-")

            if len(Datefields) == 3:
                tempDate = datetime.date(year=int(Datefields[0]), month=int(Datefields[1]), day=int(Datefields[2]))
                self.strDateOfBirth = tempDate
                return True
            else:
                return False
        except:
            return self._generalError

    def readNationality(self):
        try:
            strTemp = str(self.strNationality)
            strTemp = strTemp.strip()

            if not (strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeNationality(self, strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not (strinput == self.undefined):
                self.strNationality = strinput
                return True
            else:
                return False
        except:
            return self._generalError

class ClientsResidentialAddress(Constants):

    strResAddressLine1 = ndb.StringProperty()
    strResAddressLine2 = ndb.StringProperty()
    strCountry = ndb.StringProperty()
    strTownCity = ndb.StringProperty()
    strProvince = ndb.StringProperty()
    strPostalCode = ndb.StringProperty()


    def readResAddressL1(self):
        try:
            strTemp = str(self.strResAddressLine1)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeResAddressL1(self,strinput):
        try:
            strinput = str(strinput)
            strinput =strinput.strip()

            if not(strinput == self.undefined):
                self.strResAddressLine1 = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readResAddressL2(self):
        try:
            strTemp = str(self.strResAddressLine2)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeResAddressL2(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strResAddressLine2 = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readCityTown(self):
        try:
            strTemp = str(self.strTownCity)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeCityTown(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strTownCity = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readCountry(self):
        try:
            strTemp = str(self.strCountry)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeCountry(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCountry = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readProvince(self):
        try:
            strTemp = str(self.strProvince)
            strTemp =strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeProvince(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strProvince = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readPostalCode(self):
        try:
            strTemp = str(self.strPostalCode)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writePostalCode(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strPostalCode = strinput
                return True
            else:
                return False
        except:
            return False

class ClientsPostalAddress(Constants):

    strPostalAddressLine1 = ndb.StringProperty()
    strTownCity = ndb.StringProperty()
    strProvince = ndb.StringProperty()
    strCountry = ndb.StringProperty()
    strPostalCode = ndb.StringProperty()

    def readPostalAddressL1(self):
        try:
            strTemp = str(self.strPostalAddressLine1)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writePostalAddressL1(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strPostalAddressLine1 = strinput
                return True
            else:
                return False
        except:
            return self._generalError



    def readCountry(self):
        try:
            strTemp = str(self.strCountry)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeCountry(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCountry = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readTownCity(self):
        try:
            strTemp = str(self.strCountry)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeTownCity(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strTownCity = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readProvince(self):
        try:
            strTemp = str(self.strProvince)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeProvince(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strProvince = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readPostalCode(self):
        try:
            strTemp = str(self.strPostalCode)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writePostalCode(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()


            if not(strinput == self.undefined):
                self.strPostalCode = strinput
                return True
            else:
                return False
        except:
            return self._generalError

class ClientsContactDetails(Constants):
    """
        # Reference of CLient If relate to a policy and policy number will be shown
        # Reference of employee if its contact of an employee
    """

    strCell = ndb.StringProperty()
    strTel = ndb.StringProperty()
    strEmail = ndb.StringProperty()

    def readCell(self):
        try:
            strTemp = str(self.strCell)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeCell(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCell = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readTell(self):
        try:
            strTemp = str(self.strTel)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeTel(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strTel = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readEmail(self):
        try:
            strTemp = str(self.strEmail)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeEmail(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strEmail = strinput
                return True
            else:
                return False
        except:
            return False

class BankingDetails(Constants):
    """
        Banking Details will also take in banking details of the Employees and also that of the Clients.
    """
    strBankName = ndb.StringProperty()
    strAccountHolder = ndb.StringProperty()
    strAccountNumber = ndb.StringProperty()
    strAccountType = ndb.StringProperty(default='savings')
    strBranchCode = ndb.StringProperty()

    def readBankName(self):
        try:
            strTemp = str(self.strBankName)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeBankName(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strBankName = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readAccountHolder(self):
        try:
            strTemp = str(self.strAccountHolder)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeAccountHolder(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()
            if not(strinput == self.undefined):
                self.strAccountHolder = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readAccountNumber(self):
        try:
            strTemp = str(self.strAccountNumber)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeAccountNumber(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strAccountNumber = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def writeAccountType(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strAccountType = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readAccountType(self):
        try:
            strTemp = str(self.strAccountType)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def readBranchCode(self):
        try:
            strTemp = str(self.strBranchCode)
            strTemp = str(strTemp)

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeBranchCode(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strBranchCode = strinput
                return True
            else:
                return False
        except:
            return self._generalErr

class ClientsPersonalDetails(PersonalDetails):

    strRelationship = ndb.StringProperty()

    def readRelationship(self):
        try:
            strTemp = str(self.strRelationship)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeRelationship(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()
            if not(strinput == self.undefined):
                self.strRelationship = strinput
                return True
            else:
                return False
        except:
            return self._generalError

class Beneficiary(ClientsPersonalDetails):

    def addBeneficiary(self):
        pass

class ExtendedFamily(ClientsPersonalDetails):
    strBenefit = ndb.StringProperty()
    strPremium = ndb.StringProperty()

    def readBenefit(self):
        try:
            strTemp = str(self.strBenefit)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeBenefit(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strBenefit = strinput
                return True
            else:
                return False
        except:
            return self._generalError

    def readPremium(self):
        try:
            strTemp = str(self.strPremium)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writePremium(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strPremium = strinput
                return True
            else:
                return False
        except:
            return self._generalError

class ChildrenDetails(ClientsPersonalDetails):

   def addChild(self,strinput):
       pass

class Spouses(ClientsPersonalDetails):

    def addSpouse(self,strinput):
        pass



class Claims(ClientsPersonalDetails):
    strClaimAmount = ndb.StringProperty()
    strClaimTotalPaid = ndb.StringProperty()
    strClaimForID = ndb.StringProperty()
    strDatePaid = ndb.DateProperty()
    strClaimStatus = ndb.StringProperty() # Not Processed / Processed / Paid Out / Not Paid

    def readClaimAmount(self):
        try:
            strTemp = str(self.strClaimAmount)
            strTemp = strTemp.strip()

            if strTemp.isdigit():
                return int(strTemp)
            else:
                return ""
        except:
            return ""

    def writeClaimAmount(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if strinput.isdigit():
                self.strClaimAmount = int(strinput)
                return True
            else:
                return False
        except:
            return False

    def readClaimTotalPaid(self):
        try:
            strTemp = str(self.strClaimTotalPaid)
            strTemp = strTemp.strip()

            if strTemp.isdigit():
                return int(strTemp)
            else:
                return ""
        except:
            return ""

    def writeClaimTotalPaid(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if strinput.isdigit():
                self.strClaimTotalPaid = int(strinput)
                return True
            else:
                return False
        except:
            return False

    def readDatePaid(self):
        try:

            strTemp = str(self.strDatePaid)
            return strTemp
        except:
            return ""

    def writeDatePaid(self,strinput):
        try:
            DateList = str(strinput).split("-")
            year = DateList[0]
            month = DateList[1]
            day = DateList[2]

            thisDate = datetime.date(year=int(year),month=int(month),day=int(day))

            self.strDatePaid = thisDate
            return True
        except:
            return False

    def readClaimStatus(self):
        try:
            strTemp = str(self.strClaimStatus)
            strTemp = strTemp.lower()
            # Not Processed / Processed / Paid Out / Not Paid
            if (strTemp == "not processed") or (strTemp == "processed") or (strTemp == "paid out") or (strTemp == "not paid"):
                return strTemp.title()
            else:
                return ""
        except:
            return ""

    def writeClaimStatus(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.lower()
            if (strinput == "not processed") or (strinput == "processed") or (strinput == "paid out") or (strinput == "not paid"):
                self.strClaimStatus = strinput.title()
                return True
            else:
                return False
        except:
            return False

    def readClaimForID(self):
        try:
            strTemp = str(self.strClaimForID)
            strTemp = strTemp.strip()

            if strTemp.isdigit():
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeClaimForID(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if strinput.isdigit():
                self.strClaimForID = strinput
                return True
            else:
                return False

        except:
            return False







class PaymentHistory(ndb.Expando):

    strPaymentCode = ndb.StringProperty() # Transaction Code
    strPaymentAmount = ndb.IntegerProperty()
    strFirstPaymentDate = ndb.DateProperty()
    strIndex = ndb.IntegerProperty(default=1)
    strPaymentMethod = ndb.StringProperty(default="Cash") # Direct Deposit - Cash - Payroll Deduction - Debit Order - Persal Deduction - Intermediary
    strPayForMonth = ndb.StringProperty() # 1 .. 12
    strPayYear = ndb.IntegerProperty()
    strDatePaymentMade = ndb.DateTimeProperty()

    def readPayYear(self):
        try:
            strTemp = str(self.strPayYear)
            if strTemp.isdigit():
                return int(strTemp)
            else:
                return ""
        except:
            return ""

    def writePayYear(self,strinput):
        try:
            strinput = str(strinput)
            if strinput.isdigit():
                self.strPayYear = int(strinput)
                return True
            else:
                return False

        except:
            return False

    def readPayforMonth(self):
        try:
            strTemp = str(self.strPayForMonth)
            strTemp = strTemp.strip()

            if strTemp in strValidMonths:
                return strTemp
            else:
                return ""
        except:
            return ""

    def writePayForMonth(self,strinput):
        try:
            strinput = str(strinput)
            self.strPayForMonth = strinput
            return True
        except:
            return False



    def writePaymentMethod(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()
            strinput = strinput.lower()

            if (strinput == "cash") or (strinput == "direct deposit") or (strinput == "debit order"):
                self.strPaymentMethod = strinput.title()
                return True
            else:
                return False
        except:
            return False

    def readPaymentMethod(self):
        try:
            strTemp = str(self.strPaymentMethod)
            strTemp = strTemp.strip()
            strTemp = strTemp.lower()
            return strTemp
        except:
            return ""




    def writeFirstPaymentDate(self,strinput):
        try:
            strinput = str(strinput)
            DateList = strinput.split("/")
            year = DateList[0]
            month = DateList[1]
            day = DateList[2]

            thisDate = datetime.date(year=int(year),month=int(month),day=int(day))
            self.strFirstPaymentDate= thisDate
            return True
        except:
            return False


    def readFirstPaymentDate(self):
        try:
            strTemp = str(self.strFirstPaymentDate)
            return strTemp
        except:
            return ""


    def readPaymentsCode(self):
        try:
            strTemp = str(self.strPaymentCode)
            strTemp = strTemp.strip()

            if not(strTemp == None):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writePaymentsCode(self,strinput):
        try:
            strinput = str(strinput)
            self.strPaymentCode = strinput
            return True

        except:
            return False

    def readPaymentAmount(self):
        try:
            strTemp = str(self.strPaymentAmount)
            strTemp = strTemp.strip()

            if strTemp.isdigit():
                return int(strTemp)
            else:
                return ""
        except:
            return ""

    def writePaymentAmount(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if strinput.isdigit():
                self.strPaymentAmount = int(strinput)
                return True
            else:
                return False
        except:
            return False


    def readIndex(self):
        try:
            strTemp = str(self.strIndex)
            strTemp = strTemp.strip()

            if strTemp.isdigit():
                return int(strTemp)
            else:
                return ""

        except:
            return ""

    def writeIndex(self,strinput):
        try:

            strinput = str(strinput)
            strinput = strinput.strip()

            if strinput.isdigit():
                self.strIndex = int(strinput)
                return True
            else:
                return False

        except:
            return False

class Policy(Constants):
    strCoverCode = ndb.StringProperty()
    strTotalFamilyMembers = ndb.StringProperty()

    strTotalPremiums = ndb.IntegerProperty()
    strPaymentsCode = ndb.StringProperty()
    strDateActivated = ndb.DateProperty(auto_now_add=True)
    strFirstPremiumDate = ndb.DateProperty()
    strPaymentDay = ndb.IntegerProperty()
    strClientSignature = ndb.StringProperty()
    strEmployeeSignature = ndb.StringProperty()

    strPlanChoice =ndb.StringProperty()
    strExtendedPlanChoice = ndb.StringProperty()
    strSinglePlanChoice = ndb.StringProperty()

    strPaymentMethod = ndb.StringProperty() # Direct Deposit , Payroll , Debit Order, Persal Deduction, Intermediary, Declaration


    strActivatePolicy = ndb.BooleanProperty(default=False)


    def readPaymentMethod(self):
        try:
            strTemp = str(self.strPaymentMethod)
            strTemp = strTemp.strip()
            return strTemp
        except:
            return ""

    def writePaymentMethod(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strPaymentMethod = strinput
                return True
            else:
                return False
        except:
            return False


    def readActivatePolicy(self):
        try:
            strTemp = self.strActivatePolicy
            return strTemp
        except:
            return ""


    def writeActivatePolicy(self,strinput):
        try:
            if strinput == True:
                self.strActivatePolicy = True
                return True
            elif strinput == False:
                self.strActivatePolicy = False
                return True
        except:
            return False



    def readPlanChoice(self):
        try:
            strTemp = str(self.strPlanChoice)
            strTemp = strTemp.strip()
            strTemp = strTemp.upper()
            return strTemp

        except:
            return ""

    def writePlanChoice(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()
            strinput = strinput.upper()

            PlanChoicesList = []
            PlanChoicesList.append("A")
            PlanChoicesList.append("B")
            PlanChoicesList.append("C")
            PlanChoicesList.append("D")

            if (strinput in PlanChoicesList):
                self.strPlanChoice = strinput
                return True
            else:
                return False

        except:
            return False

    def readExtendedPlanChoice(self):
        try:
            strTemp = str(self.strExtendedPlanChoice)
            strTemp = strTemp.strip()
            strTemp = strTemp.upper()
            return strTemp

        except:
            return ""

    def writeExtendedPlanChoice(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()
            strinput = strinput.upper()
            PlanChoicesList = []
            PlanChoicesList.append("A")
            PlanChoicesList.append("B")
            PlanChoicesList.append("C")
            PlanChoicesList.append("D")

            if (strinput in PlanChoicesList):
                self.strExtendedPlanChoice = strinput
                return True
            else:
                return False

        except:
            return False

    def readSinglePlanChoice(self):
        try:
            strTemp = str(self.strSinglePlanChoice)
            strTemp = strTemp.strip()
            strTemp = strTemp.upper()
            return strTemp

        except:
            return ""


    def writeSinglePlanChoice(self,strinput):
        try:
            strinput = str(strinput)
            strinput =  strinput.strip()
            strinput = strinput.upper()
            PlanChoicesList = []
            PlanChoicesList.append("A")
            PlanChoicesList.append("B")
            PlanChoicesList.append("C")
            PlanChoicesList.append("D")

            if (strinput in PlanChoicesList):
                self.strSinglePlanChoice = strinput
                return True
            else:
                return False
        except:
            return False


    def readPaymentDay(self):
        try:
            strTemp = str(self.strPaymentDay)
            if strTemp.isdigit():
                return int(strTemp)
            else:
                return ""
        except:
            return ""

    def writePaymentDay(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()
            if strinput.isdigit():
                self.strPaymentDay = int(strinput)
                return True
            else:
                return False

        except:
            return False

    def readClientSignature(self):
        try:
            strTemp = str(self.strClientSignature)
            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeClientSignature(self,strinput):
        try:
            strinput = str(strinput)
            if not(strinput == self.undefined):
                self.strClientSignature = strinput
                return True
            else:
                return False
        except:
            return False

    def readEmployeeSignature(self):
        try:
            strTemp = str(self.strEmployeeSignature)
            return strTemp
        except:
            return ""

    def writeEmployeeSignature(self,strinput):
        try:
            strinput = str(strinput)
            if not(strinput == self.undefined):
                self.strEmployeeSignature = strinput
                return True
            else:
                return False
        except:
            return False



    def readCoverCode(self):
        try:
            strTemp = str(self.strCoverCode)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""


    def writeCoverCode(self,strinput):

        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strCoverCode = strinput
                return True
            else:
                return False
        except:
            return False


    def readTotalPremiums(self):
        try:

            strTemp = str(self.strTotalPremiums)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return int(strTemp)
            else:
                return ""
        except:
            return ""

    def writeTotalPremiums(self,strinput):
        try:

            strinput = str(strinput)
            strinput = strinput.strip()

            if strinput.isdigit():
                self.strTotalPremiums = int(strinput)
                return True
            else:
                return False
        except:
            return False

    def readPaymentsCode(self):
        try:
            strTemp = str(self.strPaymentsCode)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writePaymentCode(self,strinput):
        try:
            strinput = str(strinput)
            strinput = strinput.strip()

            if not(strinput == self.undefined):
                self.strPaymentsCode = strinput
                return True
            else:
                return False
        except:
            return False

    def readDateActivated(self):
        try:
            strTemp = str(self.strDateActivated)
            strTemp = strTemp.strip()

            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""

    def writeFirstPremiumDate(self,strinput):
        """
            1979-04-24
        :param strinput:
        :return:
        """
        try:
            if not(strinput == self.undefined):
                self.strFirstPremiumDate = strinput.date()
                return True
            else:
                return False

        except:
            return False

    def readFirstPremiumDate(self):
        try:
            strTemp = self.strFirstPremiumDate


            if not(strTemp == self.undefined):
                return strTemp
            else:
                return ""
        except:
            return ""











class AppClients (ClientsPersonalDetails):
    """
        CLients that need the ability to sign into the system needs to supply a valid Google Email Address, if not
        supplied the client will not be able to sign into the system

        strContactDetails = ndb.StructuredProperty(ContactDetails, repeated=True)
        strResidentialAddress = ndb.StructuredProperty(ResidentialAddress, repeated=True)
        strPostalAddress =ndb.StructuredProperty(PostalAddress, repeated=True)
        strBankingDetails = ndb.StructuredProperty(BankingDetails, repeated=True)

        strResourceAccessRights = ndb.StructuredProperty(ResourceAccessRights, repeated=True)
        strUserRights = ndb.StructuredProperty(UserRights, repeated=True)
    """
    def addClient(self,strinput):
        pass