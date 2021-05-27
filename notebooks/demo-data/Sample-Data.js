import React, { Component, useState, useEffect, useCallback } from "react";

class Draggable extends Component {
    constructor(props) {
        super(props);

        this.state = {
            dragEnabled: false,
            dragStart: null
        };

        this.onMouseDown = this.onMouseDown.bind(this);
        this.onMouseUp = this.onMouseUp.bind(this);
        this.onMouseMove = this.onMouseMove.bind(this);
    }
    onMouseUp(e) {
        document.removeEventListener("mousemove", this.onMouseMove, true);
        document.removeEventListener("mouseup", this.onMouseUp, true);
    }
    componentWillUnmount() {
        document.removeEventListener("mousemove", this.onMouseMove, true);
        document.removeEventListener("mouseup", this.onMouseUp, true);
    }
    onMouseMove(e) {
        const dx = e.clientX - this.state.dragStart.x;
        const dy = e.clientY - this.state.dragStart.y;

        if (this.props.onDrag) {
            this.props.onDrag(dx, dy);
        }
        this.setState({ dragStart: { x: e.clientX, y: e.clientY } });
        e.preventDefault();
    }
    onMouseDown(e) {
        this.setState({
            dragEnabled: true,
            dragStart: { x: e.clientX, y: e.clientY }
        });

        document.addEventListener("mousemove", this.onMouseMove, true);
        document.addEventListener("mouseup", this.onMouseUp, true);
        e.preventDefault();
    }
    render() {
        const { Elem, onDrag, ...rest } = this.props;
        return <Elem onMouseDown={this.onMouseDown} {...rest} />;
    }

}

export default Draggable;
