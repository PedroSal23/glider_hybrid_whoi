#!/usr/bin/env bash

#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#

# Runs a docker container with the image created by build-dev.bash
# Requires:
#   docker 19.03 or higher
#   an X server
# Recommended:
#   A joystick mounted to /dev/input/js0 or /dev/input/js1

# Determine the parent directory of this script, no matter how it is invoked.
PARENT_DIR="$(dirname "$(readlink -f "$BASH_SOURCE")")/.."

# Determine if we have the nvidia runtime enabled. If so, default to exposing
# all gpus.
if docker info -f '{{ range $key, $value := .Runtimes }}{{ $key }}{{ end }}' | grep nvidia; then
    GPUS="--gpus all"
fi

IMG="glider_hybrid_whoi:dev"
WORKSPACE="$PARENT_DIR"
RUN_ARGS=""

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -w|--whole-workspace)
        WORKSPACE="$(readlink -f "$PARENT_DIR/..")"
        shift
        ;;
    -i)
        IMG="$2"
        shift 2
        ;;
    --without-nvidia)
        GPUS=""
        shift
    ;;
    --nvidia)
        GPUS="--gpus all"
        shift
        ;;
    --run-args)
        RUN_ARGS="$RUN_ARGS $2"
        shift 2
        ;;
    --name)
        RUN_ARGS="$RUN_ARGS --name $2"
        shift 2
        ;;
    --)
        shift
        break
        ;;
    *)    # unknown option
        echo "Unknown option" >&2
        exit 1
        ;;
esac
done

USERID=$(id -u)
GROUPID=$(id -g)

# If we ever want to not match UIDs, setting the following env var would help.

#   -e XAUTHORITY_ENTRY="$(xauth nextract - "$DISPLAY")"

docker run -it \
  -e DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v "$WORKSPACE:/home/ros/glider_hybrid_whoi/src/glider_hybrid_whoi" \
  -v "/tmp/.X11-unix:/tmp/.X11-unix" \
  -v "/etc/localtime:/etc/localtime:ro" \
  --rm \
  --privileged \
  --security-opt seccomp=unconfined \
  -u "$USERID:$GROUPID" \
  $RUN_ARGS \
  $GPUS \
  "$IMG" \
  "$@"
