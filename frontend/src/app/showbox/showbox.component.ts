import { Component, Input } from "@angular/core";

/**
 * Component to display image centered with a dark overlay over the rest
 * of the page.
 */
@Component({
    selector: 'showbox',
    providers: [],
    styleUrls: ['./showbox.component.css'],
    templateUrl: './showbox.component.html'
})
export class ShowboxComponent {
    @Input() public src: string = '';

    public classModifier: string = 'closed';

    public onClick(event) {
        this.classModifier = this.classModifier === 'closed' ? 'open' : 'closed';
    }
}
