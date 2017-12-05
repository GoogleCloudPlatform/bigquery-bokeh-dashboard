# Copyright Google Inc. 2017
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

export BACKEND_PORT=30033

echo "Creating firewall rules..."
gcloud compute firewall-rules create gke-dashboard-demo-lb7-fw --target-tags dashboard-demo-node --allow "tcp:${BACKEND_PORT}" --source-ranges 130.211.0.0/22,35.191.0.0/16

echo "Creating health checks..."
gcloud compute health-checks create http dashboard-demo-basic-check --port $BACKEND_PORT --healthy-threshold 1 --unhealthy-threshold 10 --check-interval 60 --timeout 60

echo "Creating an instance group..."
export INSTANCE_GROUP=$(gcloud container clusters describe dashboard-demo-cluster --format="value(instanceGroupUrls)" | awk -F/ '{print $NF}')

echo "Creating named ports..."
gcloud compute instance-groups managed set-named-ports $INSTANCE_GROUP --named-ports "port${BACKEND_PORT}:${BACKEND_PORT}"

echo "Creating the backend service..."
gcloud compute backend-services create dashboard-demo-service --protocol HTTP --health-checks dashboard-demo-basic-check --port-name "port${BACKEND_PORT}" --global

echo "Connecting instance group to backend service..."
export INSTANCE_GROUP_ZONE=$(gcloud config get-value compute/zone)
gcloud compute backend-services add-backend dashboard-demo-service --instance-group $INSTANCE_GROUP --instance-group-zone $INSTANCE_GROUP_ZONE --global

echo "Creating URL map..."
gcloud compute url-maps create dashboard-demo-urlmap --default-service dashboard-demo-service

echo "Uploading SSL certificates..."
gcloud compute ssl-certificates create dashboard-demo-ssl-cert --certificate /tmp/dashboard-demo-ssl/ssl.crt --private-key /tmp/dashboard-demo-ssl/ssl.key

echo "Creating HTTPS target proxy..."
gcloud compute target-https-proxies create dashboard-demo-https-proxy --url-map dashboard-demo-urlmap --ssl-certificates dashboard-demo-ssl-cert

echo "Creating global forwarding rule..."
gcloud compute forwarding-rules create dashboard-demo-gfr --address $STATIC_IP --global --target-https-proxy dashboard-demo-https-proxy --ports 443
