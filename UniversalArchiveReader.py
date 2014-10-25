#!/usr/bin/python
# -*- coding: utf-8 -*-

import magic
import zlib

import zipfile
import rarfile
import io

import logging
import traceback
import py7zlib


class ArchiveReader(object):

	fp = None

	def __init__(self, archPath, fileContents=None):
		self.logger = logging.getLogger("Main.ArchTool")
		self.archPath = archPath

		self.fType = magic.from_file(archPath, mime=True).decode("ascii")

		#print "wholepath - ", wholePath
		if self.fType == 'application/x-rar':
			#print "Rar File"
			self.archHandle = rarfile.RarFile(self.archPath) # self.iterRarFiles()
			self.archType = "rar"
		elif self.fType == 'application/zip':
			#print "Zip File"
			try:
				if fileContents:  # Use pre-read fileContents whenever possible.
					self.archHandle = zipfile.ZipFile(io.BytesIO(fileContents))
				else:
					self.archHandle = zipfile.ZipFile(self.archPath) # self.iterZipFiles()

				self.archType = "zip"
			except zipfile.BadZipfile:
				print("Invalid zip file!")
				traceback.print_exc()
				raise ValueError
		elif self.fType == 'application/x-7z-compressed':
			#print "Zip File"
			try:
				if fileContents:  # Use pre-read fileContents whenever possible.
					self.archHandle = py7zlib.Archive7z(io.BytesIO(fileContents))
				else:
					self.fp = open(archPath, "rb")
					self.archHandle = py7zlib.Archive7z(self.fp) # self.iterZipFiles()

				self.archType = "7z"  # py7zlib.Archive7z mimics the interface of zipfile.ZipFile, so we'll use the zipfile.ZipFile codepaths

			except zipfile.BadZipfile:
				print("Invalid zip file!")
				traceback.print_exc()
				raise ValueError
		else:
			print("Returned MIME Type for file = ", self.fType )
			raise ValueError("Tried to create ArchiveReader on a non-archive file")


	def getZipFileList(self):
		names = self.archHandle.namelist()
		ret = []
		for name in names:
			if not name.endswith("/"):
				ret.append(name)

		return ret

	def getRarFileList(self):
		names = self.archHandle.namelist()
		ret = []
		for name in names:
			if not self.archHandle.getinfo(name).isdir():
				ret.append(name)

		return ret


	def get7zFileList(self):
		names = self.archHandle.getnames()
		return names


	def __iter__(self):
		try:
			if self.archType == "rar":
				for item in self.iterRarFiles():
					yield item
			elif self.archType == "zip":
				for item in self.iterZipFiles():
					yield item
			elif self.archType == "7z":
				for item in self.iter7zFiles():
					yield item
			else:
				raise ValueError("Not a known archive type. Wat")

		except TypeError:
			self.logger.error("Empty Archive Directory? Path = %s", self.archPath)
			raise

		except (rarfile.BadRarFile, zipfile.BadZipfile):
			self.logger.error("CORRUPT ARCHIVE: ")
			self.logger.error("%s", self.archPath)
			for tbLine in traceback.format_exc().rstrip().lstrip().split("\n"):
				self.logger.error("%s", tbLine)
			raise

		except (rarfile.PasswordRequired, RuntimeError):
			self.logger.error("Archive password protected: ")
			self.logger.error("%s", self.archPath)
			for tbLine in traceback.format_exc().rstrip().lstrip().split("\n"):
				self.logger.error("%s", tbLine)
			raise


		except zlib.error:
			self.logger.error("Archive password protected: ")
			self.logger.error("%s", self.archPath)
			for tbLine in traceback.format_exc().rstrip().lstrip().split("\n"):
				self.logger.error("%s", tbLine)
			raise

		except (KeyboardInterrupt, SystemExit, GeneratorExit):
			raise

		except:
			self.logger.error("Unknown error in archive iterator: ")
			self.logger.error("%s", self.archPath)
			for tbLine in traceback.format_exc().rstrip().lstrip().split("\n"):
				self.logger.error("%s", tbLine)
			raise

	def getFileContentHandle(self, fileName):
		return self.archHandle.open(fileName)


	def iter7zFiles(self):
		names = self.get7zFileList()
		for name in names:
			tempFp = self.archHandle.getmember(name)
			yield name, tempFp

	def iterZipFiles(self):
		names = self.getZipFileList()
		for name in names:
			with self.archHandle.open(name) as tempFp:
				yield name, tempFp



	def iterRarFiles(self):
		names = self.getRarFileList()
		for name in names:
			with self.archHandle.open(name) as tempFp:
				name = name.replace("\\", "/")
				yield name, tempFp

				#raise


	def close(self):
		# 7z files don't maintain their own file pointers
		if self.archType != "7z":
			self.archHandle.close()

		if self.fp:
			self.fp.close()
