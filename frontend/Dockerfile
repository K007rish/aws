FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
ENV Backend_API_URL=publicip:8000/api
EXPOSE 3000
ENTRYPOINT [ "npm" ]
CMD [ "start" ]