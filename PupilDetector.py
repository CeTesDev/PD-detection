# Eye Centre Localisation using Means of Gradients
# Implementation of paper by Fabian Timm and Erhardt Barth
# "Accurate Eye Centre Localisation by Means of Gradients"

# Author: Jonne Engelberts
# Increase speed by setting threshold lower and step higher.
# Threshold is the percentile of bright area included.
# Step is the amount of pixels initially skipped.

import numpy as np
from matplotlib import pyplot as plt
from scipy.ndimage.filters import gaussian_filter

class GradientIntersect:

	def __init__(self, (height, width), threshold=100, step=1):

		self.height = height
		self.width = width
		self.grid = self.createGrid(height, width)
		self.area = threshold
		self.accuracy = step

	def createGrid(self, Y, X):
    
		# create grid vectors
		grid = np.array([[y,x] for y in range(1-Y,Y) for x in range (1-X,X)], dtype='float')

		# normalize grid vectors
		grid2 = np.sqrt(np.einsum('ij,ij->i',grid,grid))
		grid2[grid2==0] = 1
		grid /= grid2[:,np.newaxis]

		# reshape grid for easier displacement selection
		grid = grid.reshape(Y*2-1,X*2-1,2)
		
		# return values
		return grid

	def locate(self, image):
		
		# get image size
		Y, X = image.shape
		
		# create empty score matrix
		scores = np.zeros((Y,X))

		# normalize image
		image = (image.astype('float') - np.min(image)) / np.max(image)

		# blur image
		blurred = gaussian_filter(image, sigma=5)
		retain = np.percentile(blurred, self.area)

		# calculate gradients
		gy, gx = np.gradient(image)
		gx = np.reshape(gx, (X*Y,1))
		gy = np.reshape(gy, (X*Y,1))
		gradient = np.hstack((gy,gx))

		# normalize gradients
		gradient2 = np.sqrt(np.einsum('ij,ij->i',gradient,gradient))
		gradient2[gradient2==0] = 1
		gradient /= gradient2[:,np.newaxis]

		# loop through all pixels
		for cy in range(0,Y,self.accuracy):
			for cx in range(0,X,self.accuracy):

				if image[cy,cx] < retain:

					# select displacement
					displacement = self.grid[Y-cy-1:Y*2-cy-1,X-cx-1:X*2-cx-1,:]
					displacement = np.reshape(displacement,(X*Y,2))

					# calculate score
					score = np.einsum('ij,ij->i', displacement, gradient)
					score = np.einsum('i,i->', score, score)
					scores[cy,cx] = score

		# multiply with the blurred darkness
		scores = scores * (1-blurred)

		# if we skipped pixels, get more accurate around the best pixel
		if self.accuracy>1:

			# get maximum value index 
			(yval,xval) = np.where(scores==np.max(scores))

			# loop through new pixels
			for cy in range(yval-self.accuracy,yval+self.accuracy+1):
				for cx in range(xval-self.accuracy,xval+self.accuracy+1):

					# select displacement
					displacement = grid[Y-cy-1:Y*2-cy-1,X-cx-1:X*2-cx-1,:]
					displacement = np.reshape(displacement,(X*Y,2))

					# calculate score
					score = np.einsum('ij,ij->i', displacement, gradient)
					score = np.einsum('i,i->', score, score)
					scores[cy,cx] = score * (1-blurred[cy,cx])

		# get maximum value index 
		(yval,xval) = np.where(scores==np.max(scores))
		
		# return values
		return (yval, xval)